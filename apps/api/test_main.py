"""Unit tests for the turn pipeline. No API key and no network:

    python3 -m unittest apps.api.test_main

classify and respond are patched, so these assert the orchestration around the
model calls rather than the model's output.
"""

import asyncio
import os
import queue
import re
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
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
        # A turn passes the client into classify and respond, so the argument is
        # built even though both are patched, and the SDK refuses to build one
        # without a key. Standing in for it is what keeps this run keyless.
        self._client_patch = patch.object(main, "get_client", return_value=object())
        self._client_patch.start()

    def tearDown(self):
        self._client_patch.stop()
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
    paper, antibody-characterization carries three, and one of those is the
    same Uhlén 2016 that what-is-binding cites alongside the Janeway glossary.
    A reply touching all three has to reuse the shared paper rather than number
    it twice, and leave nothing dangling.

    The coupling is deliberate and these assertions are expected to move when
    the corpus does. They last moved when IPI-authored concepts began citing
    IPI's own public quality page, which is why the last test below asserts
    exclusivity rather than silence: the framework sentence used to render
    nothing because IPI published nothing to point at, and now renders one
    source, still never a neighbor's.
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
            " Characterization describes the reagent [2, 3, 4]."
            " Binding is the interaction itself [3, 5]."
            " IPI reads all of it one way [6].",
        )

    def test_rows_resolve_to_the_papers_the_numbers_name(self):
        # Janeway appears twice by design: what-is-an-antibody cites the
        # antibody-antigen chapter, what-is-binding cites the glossary for the
        # avidity definition. Same book, different sections, different URLs, so
        # they are two rows the titles tell apart rather than one shared source.
        shorts = [s.get("short") for s in self.done["sources"]]
        self.assertEqual(
            shorts,
            ["Janeway 2001", "Ayoubi 2025", "Uhlén 2016", "Kahn 2024",
             "Janeway 2001", "IPI Quality"],
        )
        titles = [s.get("title") for s in self.done["sources"]]
        self.assertNotEqual(titles[0], titles[4])

    def test_an_ipi_claim_cites_only_ipi(self):
        # The framework sentence carries IPI's own page and nothing else. The
        # concepts cited beside it in this reply hold four external papers
        # between them, and not one of them attaches to IPI's claim.
        last = self.visible.rsplit(".", 2)[-2]
        ordinals = [int(n) for group in re.findall(r"\[([\d, ]+)\]", last)
                    for n in group.split(",")]
        self.assertEqual(len(ordinals), 1)
        cited = self.done["sources"][ordinals[0] - 1]
        self.assertEqual(cited["short"], "IPI Quality")
        self.assertIn("proteininnovation.org", cited["url"])


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


class FeedbackTests(TurnHarness, unittest.TestCase):
    """A thumbs verdict reaches the trace and nothing else.

    Feedback arrives on its own request, so it carries none of the turn's
    context and has to stand on the same same-origin refusal. It also has to
    survive a session the server no longer holds: sessions live in memory, a
    restart clears them, and the visitor's opinion is still the datum.
    """

    def setUp(self):
        super().setUp()
        main.SESSIONS[self.session.session_id] = self.session
        self.client = TestClient(main.app)

    def tearDown(self):
        main.SESSIONS.pop(self.session.session_id, None)
        super().tearDown()

    def post(self, payload=None, headers=None):
        body = {"session_id": self.session.session_id, "turn_index": 0, "verdict": "up"}
        body.update(payload or {})
        return self.client.post("/feedback", json=body, headers=headers)

    def test_both_verdicts_are_accepted(self):
        for verdict in ("up", "down"):
            self.assertEqual(self.post({"verdict": verdict}).status_code, 204, verdict)

    def test_span_carries_the_verdict_and_the_turn_it_judges(self):
        self.post({"turn_index": 2, "verdict": "down"})
        span = self.spans()["abbie.feedback"]
        self.assertEqual(span["gen_ai.conversation.id"], "sess-test")
        self.assertEqual(span["abbie.turn_index"], 2)
        self.assertEqual(span["gen_ai.evaluation.name"], "user_feedback")
        self.assertEqual(span["gen_ai.evaluation.score.label"], "down")
        self.assertTrue(span["abbie.session_live"])

    def test_verdict_for_a_forgotten_session_is_kept_and_marked(self):
        response = self.post({"session_id": "sess-gone-after-restart"})
        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.spans()["abbie.feedback"]["abbie.session_live"])

    def test_unknown_verdict_is_refused(self):
        response = self.post({"verdict": "sideways"})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("abbie.feedback", self.spans())

    def test_cross_origin_verdict_is_refused(self):
        response = self.post(headers={"origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("abbie.feedback", self.spans())

    def test_the_page_s_own_origin_is_accepted(self):
        response = self.post(headers={"origin": "http://localhost:8811"})
        self.assertEqual(response.status_code, 204)


async def run_startup(app) -> None:
    """Drive the app's startup the way an ASGI server does.

    TestClient's context manager runs the same hooks, but its portal reports a
    SystemExit escaping them as a cancellation, which hides both the type and
    the message. Speaking the lifespan protocol directly shows what uvicorn
    sees.
    """

    async def receive():
        return {"type": "lifespan.startup"}

    async def send(message):
        return None

    await app({"type": "lifespan", "asgi": {"version": "3.0"}}, receive, send)


class ApiKeyGateTests(unittest.TestCase):
    """The key is required to serve, not to import.

    This suite and any tooling that reads the module import it with no key and
    no network, so the check belongs on the server's startup. What it must not
    lose is the fail-fast: a keyless uvicorn still has to stop at the door
    rather than answer requests and fail one turn at a time.
    """

    def tearDown(self):
        main.get_client.cache_clear()

    def test_missing_key_refuses_to_start(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as caught:
                main.require_api_key()
        self.assertIn("OPENAI_API_KEY is not set", str(caught.exception))
        self.assertIn("keys.env", str(caught.exception))

    def test_a_key_in_the_environment_passes(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            self.assertIsNone(main.require_api_key())

    def test_startup_stops_the_server_without_a_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as caught:
                asyncio.run(run_startup(main.app))
        self.assertIn("OPENAI_API_KEY is not set", str(caught.exception))

    def test_every_turn_shares_one_client(self):
        main.get_client.cache_clear()
        with patch("openai.OpenAI") as constructor:
            first = main.get_client()
            second = main.get_client()
        self.assertIs(first, second)
        self.assertEqual(constructor.call_count, 1)


if __name__ == "__main__":
    unittest.main()
