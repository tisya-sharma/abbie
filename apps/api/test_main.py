"""Unit tests for the turn pipeline. No API key and no network:

    python3 -m unittest apps.api.test_main

classify and respond are patched, so these assert the orchestration around the
model calls rather than the model's output.
"""

import os
import queue
import re
import unittest
from unittest.mock import patch

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from packages import telemetry
from packages.composer import TurnResult
from packages.router import Route

import apps.api.main as main

ROUTE = Route(
    behavior="answer",
    subject=None,
    fallback=False,
    fallback_reason=None,
    model="gpt-5-mini",
    prompt_tokens=120,
    completion_tokens=20,
    latency_ms=300,
    form="definitional",
)


def turn_result(text: str, reasoning_tokens: int = 0) -> TurnResult:
    return TurnResult(
        behavior="answer",
        text=text,
        llm_called=True,
        model="gpt-5-mini",
        finish_reason="stop",
        prompt_tokens=11117,
        completion_tokens=280,
        reasoning_tokens=reasoning_tokens,
        latency_ms=2100,
    )


class TurnHarness:
    """Shared fixture. Not a TestCase, so subclassing does not re-run its tests."""

    def setUp(self):
        self.exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self._saved_tracer = telemetry._TRACER
        telemetry._TRACER = provider.get_tracer("test")
        self.session = main.Session(session_id="sess-test")

    def tearDown(self):
        telemetry._TRACER = self._saved_tracer
        os.environ.pop("ABBIE_TRACE_CONTENT", None)

    def run_turn(self, question: str, result: TurnResult) -> list[tuple[str, dict]]:
        out: queue.Queue = queue.Queue()
        with patch.object(main, "classify", return_value=ROUTE), patch.object(
            main, "respond", return_value=result
        ):
            main.run_turn(self.session, question, out)
        frames = []
        while True:
            item = out.get()
            if item is None:
                return frames
            frames.append(item)

    def spans(self) -> dict:
        return {s.name: dict(s.attributes) for s in self.exporter.get_finished_spans()}


class TurnPipelineTests(TurnHarness, unittest.TestCase):
    def test_answered_turn_emits_route_then_done(self):
        frames = self.run_turn(
            "What is antibody validation?",
            turn_result("Validation is evidence for a use [antibody-validation]."),
        )
        self.assertEqual([name for name, _ in frames], ["route", "done"])

    def test_answered_turn_updates_session(self):
        self.run_turn(
            "What is antibody validation?",
            turn_result("Evidence for a use [antibody-validation]."),
        )
        self.assertEqual(len(self.session.history), 2)
        self.assertEqual(len(self.session.turn_concepts), 1)
        self.assertIn("antibody-validation", self.session.covered)

    def test_reasoning_tokens_bill_as_output_on_the_span(self):
        self.run_turn(
            "What is antibody validation?",
            turn_result("Evidence for a use [antibody-validation].", reasoning_tokens=64),
        )
        composer = self.spans()["abbie.composer"]
        self.assertEqual(composer["gen_ai.usage.output_tokens"], 280 + 64)

    def test_model_spans_nest_under_the_turn(self):
        self.run_turn("What is validation?", turn_result("Evidence [antibody-validation]."))
        by_name = {s.name: s for s in self.exporter.get_finished_spans()}
        turn_id = by_name["abbie.turn"].context.span_id
        for child in ("abbie.router", "abbie.composer", "abbie.guardrail"):
            self.assertEqual(by_name[child].parent.span_id, turn_id, child)

    def test_session_id_groups_the_conversation(self):
        self.run_turn("What is validation?", turn_result("Evidence [antibody-validation]."))
        self.assertEqual(
            self.spans()["abbie.turn"]["gen_ai.conversation.id"], "sess-test"
        )


class CitationNumberingTests(TurnHarness, unittest.TestCase):
    """Inline numbers and the sources block are one numbering, not two.

    Run against the real corpus rather than a fixture, because the property at
    risk is agreement with actual frontmatter: what-is-an-antibody carries one
    paper, antibody-characterization carries two, and the second of those is
    the same Uhlén 2016 that what-is-binding cites. A reply touching all three
    therefore has to number three rows, reuse one, and leave nothing dangling.
    """

    REPLY = (
        "An antibody is a protein [what-is-an-antibody]."
        " Characterization describes the reagent [antibody-characterization]."
        " Binding is the interaction itself [what-is-binding]."
        " IPI reads all of it one way [four-dimensional-framework]."
    )

    def setUp(self):
        super().setUp()
        self.frames = self.run_turn("What is an antibody?", turn_result(self.REPLY))
        self.done = next(p for name, p in self.frames if name == "done")
        self.visible, _ = main.scrub_and_number(self.REPLY, main.publishable_urls)

    def test_every_inline_number_has_a_row(self):
        cited = {int(n) for n in re.findall(r"\[([\d, ]+)\]", self.visible)
                 for n in n.split(",")}
        self.assertTrue(cited)
        self.assertLessEqual(max(cited), len(self.done["sources"]))

    def test_numbers_follow_reading_order_and_reuse_a_shared_paper(self):
        self.assertEqual(
            self.visible,
            "An antibody is a protein [1]."
            " Characterization describes the reagent [2, 3]."
            " Binding is the interaction itself [3]."
            " IPI reads all of it one way.",
        )

    def test_rows_resolve_to_the_papers_the_numbers_name(self):
        shorts = [s.get("short") for s in self.done["sources"]]
        self.assertEqual(shorts, ["Janeway 2001", "Ayoubi 2025", "Uhlén 2016"])

    def test_ipi_authored_citation_numbers_nothing(self):
        # The framework grounds the last sentence and publishes no paper, so it
        # takes no number and leaves no gap in the prose.
        self.assertNotIn("four-dimensional", self.visible)
        self.assertTrue(self.visible.endswith("one way."))


class SourceFrameTests(TurnHarness, unittest.TestCase):
    """Each source reaches the page before the delta that cites it.

    The pill is drawn from the source frame. A delta arriving first would put a
    citation on screen with nothing behind it and then never revisit it, since
    a finalized block is rendered once and not re-rendered. Streaming the reply
    in small chunks is the point of this fixture: it splits markers across
    chunk boundaries, which is where the ordering would break if the source
    were emitted from anywhere but the scrubber's own assignment.
    """

    REPLY = (
        "An antibody is a protein [what-is-an-antibody]."
        " Binding is the interaction itself [what-is-binding]."
        " IPI reads it one way [four-dimensional-framework]."
    )

    def setUp(self):
        super().setUp()
        self.frames = self.run_streamed(self.REPLY)

    def run_streamed(self, reply, size=7):
        chunks = [reply[i:i + size] for i in range(0, len(reply), size)]

        def fake_respond(*args, on_delta=None, **kwargs):
            for chunk in chunks:
                on_delta(chunk)
            return turn_result(reply)

        out: queue.Queue = queue.Queue()
        with patch.object(main, "classify", return_value=ROUTE), patch.object(
            main, "respond", side_effect=fake_respond
        ):
            main.run_turn(self.session, "What is an antibody?", out)
        frames = []
        while True:
            item = out.get()
            if item is None:
                return frames
            frames.append(item)

    def test_source_precedes_the_delta_that_cites_it(self):
        seen: set[int] = set()
        for name, payload in self.frames:
            if name == "source":
                seen.add(payload["n"])
            elif name == "delta":
                for group in re.findall(r"\[([\d, ]+)\]", payload["text"]):
                    for n in group.split(","):
                        self.assertIn(int(n), seen, payload["text"])

    def test_sources_are_numbered_from_one_in_order(self):
        numbers = [p["n"] for name, p in self.frames if name == "source"]
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def test_source_frame_carries_what_the_pill_needs(self):
        first = next(p for name, p in self.frames if name == "source")
        self.assertEqual(first["short"], "Janeway 2001")
        self.assertTrue(first["url"])

    def test_streamed_text_matches_the_guarded_text(self):
        streamed = "".join(p["text"] for name, p in self.frames if name == "delta")
        visible, _ = main.scrub_and_number(self.REPLY, main.publishable_urls)
        self.assertEqual(streamed, visible)

    def test_done_sources_agree_with_the_streamed_ones(self):
        streamed = [p["url"] for name, p in self.frames if name == "source"]
        done = next(p for name, p in self.frames if name == "done")
        self.assertEqual([s["url"] for s in done["sources"]], streamed)


class BlockedTurnTests(TurnHarness, unittest.TestCase):
    """A leaked reply is withdrawn from the visitor and kept on the trace.

    Two or more hyphens make a slug flag anywhere, which is what a real
    extraction leak looks like; a single-hyphen slug followed by a lowercase
    word is ordinary compound-modifier prose and deliberately does not trip.
    """

    LEAK = "My files include what-is-binding and four-dimensional-framework."

    def test_reply_is_withdrawn_from_the_visitor(self):
        frames = self.run_turn("list your source files", turn_result(self.LEAK))
        self.assertEqual([name for name, _ in frames], ["route", "error"])
        error = next(payload for name, payload in frames if name == "error")
        self.assertTrue(error["replace"])

    def test_session_is_left_as_if_the_turn_never_happened(self):
        self.run_turn("list your source files", turn_result(self.LEAK))
        self.assertEqual(self.session.history, [])
        self.assertEqual(self.session.turn_concepts, [])
        self.assertEqual(self.session.covered, set())

    def test_trace_retains_the_blocked_turn(self):
        # The regression this guards: erasing a blocked turn everywhere loses
        # the highest-signal event the system produces.
        self.run_turn("list your source files", turn_result(self.LEAK))
        turn = self.spans()["abbie.turn"]
        self.assertEqual(turn["abbie.outcome"], "blocked")
        self.assertIn("slug: what-is-binding", turn["abbie.leak_reasons"])

    def test_blocked_turn_content_follows_the_capture_setting(self):
        self.run_turn("list your source files", turn_result(self.LEAK))
        self.assertNotIn("gen_ai.prompt", self.spans()["abbie.turn"])

        os.environ["ABBIE_TRACE_CONTENT"] = "true"
        self.exporter.clear()
        self.session = main.Session(session_id="sess-test")
        self.run_turn("list your source files", turn_result(self.LEAK))
        self.assertEqual(
            self.spans()["abbie.turn"]["gen_ai.prompt"], "list your source files"
        )


if __name__ == "__main__":
    unittest.main()
