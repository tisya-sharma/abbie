"""Unit tests for the bounded tool loop. Run without an API key:

    python3 -m unittest packages.agent.test_agent

Every client here is hand-rolled on types.SimpleNamespace and returns canned
objects. Nothing in this file reaches a network.
"""

import os
import types
import unittest

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from packages import telemetry
from packages.agent import BUDGET_NOTE, MAX_TOOL_CALLS, run_answer_loop
from packages.agent.tools import ToolRegistry, antibody_registry, run_tool
from packages.antibody import GetAntibodyArgs
from packages.composer import (
    TOOL_LOOP_ENV,
    ComposerPrompts,
    respond,
    tool_loop_enabled,
)
from packages.guardrail import CitedSources, leak_scan, scrub_and_number
from packages.router import Route

PROMPTS = ComposerPrompts(
    answer_system="answer system",
    redirect_system="redirect system",
    refuse_text="refuse",
    abstain_template="abstain {subject}",
)

QUESTION = "what do you have against EXAMPLEGENE1"
MESSAGES = [{"role": "user", "content": QUESTION}]


def route(behavior: str, subject: str | None = None) -> Route:
    return Route(
        behavior=behavior, subject=subject, fallback=False, fallback_reason=None,
        model="stub", prompt_tokens=0, completion_tokens=0, latency_ms=0, form=None,
    )


def usage(prompt: int = 10, completion: int = 5, reasoning: int = 1):
    return types.SimpleNamespace(
        prompt_tokens=prompt,
        completion_tokens=completion,
        completion_tokens_details=types.SimpleNamespace(reasoning_tokens=reasoning),
    )


def tool_call(call_id: str, name: str, arguments: str):
    return types.SimpleNamespace(
        id=call_id,
        type="function",
        function=types.SimpleNamespace(name=name, arguments=arguments),
    )


def reply(content: str | None, calls=()):
    choice = types.SimpleNamespace(
        message=types.SimpleNamespace(content=content, tool_calls=list(calls)),
        finish_reason="tool_calls" if calls else "stop",
    )
    return types.SimpleNamespace(choices=[choice], usage=usage())


class ScriptedClient:
    """Returns canned responses in order, recording what it was asked for.

    The last response repeats once the script runs out, which is how a client
    that never stops asking for a tool is expressed without writing an infinite
    list.
    """

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[dict] = []
        outer = self

        class Completions:
            def create(self, **kwargs):
                outer.calls.append(kwargs)
                index = min(len(outer.calls) - 1, len(outer.responses) - 1)
                return outer.responses[index]

        self.chat = types.SimpleNamespace(completions=Completions())

    @property
    def call_count(self) -> int:
        return len(self.calls)


def search_call(call_id: str):
    return tool_call(call_id, "search_antibodies", '{"target": "EXAMPLEGENE1"}')


def always_tools_client() -> ScriptedClient:
    """A model that requests a tool on every round, forever."""
    return ScriptedClient([reply("partial answer", [search_call("call-x")])])


class TerminationTests(unittest.TestCase):
    def test_a_reply_with_no_tool_call_ends_the_turn(self):
        client = ScriptedClient([reply("a plain answer")])
        turn = run_answer_loop(client, MESSAGES, "stub", "low")
        self.assertEqual(client.call_count, 1)
        self.assertEqual(turn.tool_calls_made, 0)
        self.assertFalse(turn.cap_reached)
        self.assertEqual(turn.result.text, "a plain answer")
        self.assertEqual(turn.result.behavior, "answer")
        self.assertTrue(turn.result.llm_called)

    def test_one_tool_round_then_prose(self):
        client = ScriptedClient(
            [reply(None, [search_call("call-1")]), reply("the composed answer")]
        )
        turn = run_answer_loop(client, MESSAGES, "stub", "low")
        self.assertEqual(client.call_count, 2)
        self.assertEqual(turn.tool_calls_made, 1)
        self.assertFalse(turn.cap_reached)
        self.assertEqual(turn.result.text, "the composed answer")

    def test_usage_is_summed_across_the_rounds(self):
        client = ScriptedClient(
            [reply(None, [search_call("call-1")]), reply("done")]
        )
        turn = run_answer_loop(client, MESSAGES, "stub", "low")
        self.assertEqual(turn.result.prompt_tokens, 20)
        self.assertEqual(turn.result.completion_tokens, 10)
        self.assertEqual(turn.result.reasoning_tokens, 2)

    def test_the_callers_messages_are_what_the_first_call_sends(self):
        """The loop composes over the composer's context, not its own."""
        client = ScriptedClient([reply("done")])
        run_answer_loop(client, MESSAGES, "stub", "low")
        self.assertEqual(client.calls[0]["messages"], MESSAGES)
        self.assertEqual(client.calls[0]["model"], "stub")
        self.assertEqual(client.calls[0]["reasoning_effort"], "low")


class CapTests(unittest.TestCase):
    """The cap is the whole reason this is a bounded loop rather than an agent."""

    def test_a_model_that_always_asks_stops_at_the_cap(self):
        client = always_tools_client()
        turn = run_answer_loop(client, MESSAGES, "stub", "low")
        self.assertEqual(turn.tool_calls_made, MAX_TOOL_CALLS)
        self.assertTrue(turn.cap_reached)
        # One call per budgeted round plus the final composing call.
        self.assertEqual(client.call_count, MAX_TOOL_CALLS + 1)

    def test_the_final_call_is_made_with_no_tools_offered(self):
        client = always_tools_client()
        run_answer_loop(client, MESSAGES, "stub", "low")
        self.assertIn("tools", client.calls[0])
        self.assertNotIn("tools", client.calls[-1])

    def test_the_exhausted_turn_returns_what_it_has(self):
        client = always_tools_client()
        turn = run_answer_loop(client, MESSAGES, "stub", "low")
        self.assertEqual(turn.result.text, "partial answer")

    def test_the_gap_is_stated_to_the_model_before_it_composes(self):
        client = always_tools_client()
        run_answer_loop(client, MESSAGES, "stub", "low")
        final = client.calls[-1]["messages"]
        self.assertEqual(
            sum(1 for m in final if m.get("content") == BUDGET_NOTE), 1
        )

    def test_surplus_calls_in_one_message_are_refused_not_run(self):
        """A model can ask for more in one message than the cap can pay for."""
        wanted = MAX_TOOL_CALLS + 2
        client = ScriptedClient(
            [
                reply(None, [search_call(f"call-{n}") for n in range(wanted)]),
                reply("done"),
            ]
        )
        turn = run_answer_loop(client, MESSAGES, "stub", "low")
        self.assertEqual(turn.tool_calls_made, MAX_TOOL_CALLS)
        self.assertEqual(len(turn.unfulfilled), 2)
        # Every requested call still gets a reply, or the conversation the next
        # request replays is malformed.
        final = client.calls[-1]["messages"]
        self.assertEqual(sum(1 for m in final if m["role"] == "tool"), wanted)

    def test_a_lower_cap_is_honored(self):
        client = always_tools_client()
        turn = run_answer_loop(client, MESSAGES, "stub", "low", max_tool_calls=2)
        self.assertEqual(turn.tool_calls_made, 2)
        self.assertEqual(client.call_count, 3)


class BehaviorSeparationTests(unittest.TestCase):
    """refuse and abstain never enter the loop, whatever the flag says.

    The separation is structural rather than a rule the loop is asked to
    respect: the composer dispatches here only after those branches returned.
    """

    def turn(self, behavior: str, client):
        return respond(
            client, route(behavior, subject="clone 4B2"), QUESTION, PROMPTS,
            "stub", "low", tool_loop=True,
        )

    def test_refuse_makes_no_call_at_all(self):
        client = always_tools_client()
        result = self.turn("refuse", client)
        self.assertEqual(client.call_count, 0)
        self.assertFalse(result.llm_called)
        self.assertEqual(result.text, "refuse")

    def test_abstain_makes_no_call_at_all(self):
        client = always_tools_client()
        result = self.turn("abstain", client)
        self.assertEqual(client.call_count, 0)
        self.assertFalse(result.llm_called)
        self.assertEqual(result.text, "abstain clone 4B2")

    def test_redirect_runs_one_call_with_no_tools(self):
        client = ScriptedClient([reply("a redirect")])
        result = self.turn("redirect", client)
        self.assertEqual(client.call_count, 1)
        self.assertNotIn("tools", client.calls[0])
        self.assertEqual(result.behavior, "redirect")

    def test_answer_is_the_only_behavior_that_reaches_the_loop(self):
        client = always_tools_client()
        result = self.turn("answer", client)
        self.assertIn("tools", client.calls[0])
        self.assertEqual(result.behavior, "answer")


class OffByDefaultTests(unittest.TestCase):
    """The loop is Stage 2 infrastructure ahead of its data, so it stays off."""

    def setUp(self):
        self._saved = os.environ.pop(TOOL_LOOP_ENV, None)

    def tearDown(self):
        os.environ.pop(TOOL_LOOP_ENV, None)
        if self._saved is not None:
            os.environ[TOOL_LOOP_ENV] = self._saved

    def test_unset_environment_means_off(self):
        self.assertFalse(tool_loop_enabled())

    def test_the_flag_is_read_from_the_environment(self):
        os.environ[TOOL_LOOP_ENV] = "true"
        self.assertTrue(tool_loop_enabled())

    def test_an_explicit_argument_wins_over_the_environment(self):
        os.environ[TOOL_LOOP_ENV] = "true"
        self.assertFalse(tool_loop_enabled(False))

    def test_an_unrecognized_value_means_off(self):
        os.environ[TOOL_LOOP_ENV] = "maybe"
        self.assertFalse(tool_loop_enabled())

    def test_the_default_answer_path_offers_no_tools_and_calls_once(self):
        client = always_tools_client()
        result = respond(client, route("answer"), QUESTION, PROMPTS, "stub", "low")
        self.assertEqual(client.call_count, 1)
        self.assertNotIn("tools", client.calls[0])
        self.assertEqual(result.text, "partial answer")

    def test_tool_calls_in_a_reply_are_ignored_when_the_loop_is_off(self):
        """A response carrying tool calls must not start a loop by accident."""
        client = always_tools_client()
        respond(client, route("answer"), QUESTION, PROMPTS, "stub", "low")
        self.assertEqual(client.call_count, 1)


class ToolFailureTests(unittest.TestCase):
    """A tool is the boundary with code the loop does not own."""

    def failing_registry(self) -> ToolRegistry:
        def explode(identifier: str):
            raise RuntimeError("the placeholder store is not there")

        base = antibody_registry()
        return ToolRegistry(
            definitions=base.definitions,
            functions={"get_antibody": explode},
            arguments={"get_antibody": GetAntibodyArgs},
        )

    def lookup_client(self) -> ScriptedClient:
        return ScriptedClient(
            [
                reply(
                    None,
                    [tool_call("call-1", "get_antibody", '{"identifier": "X"}')],
                ),
                reply("I could not check that"),
            ]
        )

    def test_a_raising_tool_does_not_kill_the_turn(self):
        client = self.lookup_client()
        turn = run_answer_loop(
            client, MESSAGES, "stub", "low", registry=self.failing_registry()
        )
        self.assertEqual(turn.result.text, "I could not check that")
        self.assertEqual(turn.tool_calls_made, 1)

    def test_the_failure_is_reported_into_the_conversation(self):
        client = self.lookup_client()
        run_answer_loop(
            client, MESSAGES, "stub", "low", registry=self.failing_registry()
        )
        tool_messages = [m for m in client.calls[-1]["messages"] if m["role"] == "tool"]
        self.assertIn("RuntimeError", tool_messages[0]["content"])

    def test_an_unknown_tool_name_degrades_rather_than_raising(self):
        payload, failed = run_tool(antibody_registry(), "get_validation_profile", "{}")
        self.assertTrue(failed)
        self.assertIn("no such tool", payload)

    def test_arguments_that_are_not_json_degrade(self):
        payload, failed = run_tool(antibody_registry(), "get_antibody", "not json")
        self.assertTrue(failed)
        self.assertIn("valid JSON", payload)

    def test_arguments_that_do_not_validate_degrade(self):
        payload, failed = run_tool(antibody_registry(), "get_antibody", "{}")
        self.assertTrue(failed)
        self.assertIn("invalid arguments", payload)

    def test_a_successful_call_reports_no_failure(self):
        payload, failed = run_tool(
            antibody_registry(), "get_antibody", '{"identifier": "PLACEHOLDER-0001"}'
        )
        self.assertFalse(failed)
        self.assertIn("PLACEHOLDER-0001", payload)


class SpanTests(unittest.TestCase):
    """Every call is a span, so cost and latency stay readable per turn."""

    def setUp(self):
        self.exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self._saved = telemetry._TRACER
        telemetry._TRACER = provider.get_tracer("test")

    def tearDown(self):
        telemetry._TRACER = self._saved

    def names(self) -> list[str]:
        return [span.name for span in self.exporter.get_finished_spans()]

    def test_one_span_per_tool_call(self):
        run_answer_loop(always_tools_client(), MESSAGES, "stub", "low")
        tool_spans = [n for n in self.names() if n.startswith("abbie.tool.")]
        self.assertEqual(len(tool_spans), MAX_TOOL_CALLS)
        self.assertEqual(set(tool_spans), {"abbie.tool.search_antibodies"})

    def test_one_span_per_model_call(self):
        run_answer_loop(always_tools_client(), MESSAGES, "stub", "low")
        model_spans = [n for n in self.names() if n == "abbie.agent.model"]
        self.assertEqual(len(model_spans), MAX_TOOL_CALLS + 1)

    def test_a_tool_span_carries_the_genai_execute_tool_attributes(self):
        client = ScriptedClient(
            [
                reply(
                    None,
                    [
                        tool_call(
                            "call-7",
                            "get_antibody",
                            '{"identifier": "PLACEHOLDER-0001"}',
                        )
                    ],
                ),
                reply("done"),
            ]
        )
        run_answer_loop(client, MESSAGES, "stub", "low")
        span = next(
            s
            for s in self.exporter.get_finished_spans()
            if s.name == "abbie.tool.get_antibody"
        )
        attrs = dict(span.attributes)
        self.assertEqual(attrs["gen_ai.operation.name"], "execute_tool")
        self.assertEqual(attrs["gen_ai.tool.name"], "get_antibody")
        self.assertEqual(attrs["gen_ai.tool.call.id"], "call-7")
        self.assertFalse(attrs["abbie.tool_failed"])

    def test_a_model_span_records_usage_for_every_round(self):
        run_answer_loop(always_tools_client(), MESSAGES, "stub", "low")
        spans = [
            s
            for s in self.exporter.get_finished_spans()
            if s.name == "abbie.agent.model"
        ]
        for span in spans:
            attrs = dict(span.attributes)
            self.assertEqual(attrs["gen_ai.usage.input_tokens"], 10)
            # Reasoning tokens bill as output and are counted there.
            self.assertEqual(attrs["gen_ai.usage.output_tokens"], 6)
        self.assertFalse(dict(spans[-1].attributes)["abbie.tools_offered"])

    def test_no_tool_span_when_the_model_asks_for_nothing(self):
        run_answer_loop(ScriptedClient([reply("plain")]), MESSAGES, "stub", "low")
        self.assertEqual([n for n in self.names() if n.startswith("abbie.tool.")], [])


class LeakScanTests(unittest.TestCase):
    """The scan runs on the final text exactly as it does now, at the API layer.

    Which means the loop's job is to hand back raw text and hide nothing from
    the backstop. A second scan in a second place is how two policies start to
    disagree, so what is asserted here is that the existing one still bites.
    """

    LEAKY = "Rests on molecular-integrity. See the kickoff notes. [what-is-binding]"

    def leaky_turn(self):
        client = ScriptedClient(
            [reply(None, [search_call("call-1")]), reply(self.LEAKY)]
        )
        return run_answer_loop(client, MESSAGES, "stub", "low")

    def test_the_loop_returns_text_unscrubbed_for_the_backstop_to_read(self):
        self.assertEqual(self.leaky_turn().result.text, self.LEAKY)

    def test_the_production_scan_flags_a_leak_the_loop_produced(self):
        turn = self.leaky_turn()
        visible, _ = scrub_and_number(turn.result.text, lambda slug: CitedSources())
        findings = leak_scan(visible, {"molecular-integrity", "what-is-binding"})
        self.assertIn("slug: molecular-integrity", findings)
        self.assertIn("internal label: kickoff notes", findings)

    def test_a_clean_loop_reply_passes_the_scan(self):
        client = ScriptedClient([reply("A clean reply about binding.")])
        turn = run_answer_loop(client, MESSAGES, "stub", "low")
        visible, _ = scrub_and_number(turn.result.text, lambda slug: CitedSources())
        self.assertEqual(leak_scan(visible, {"molecular-integrity"}), [])


class StreamingTests(unittest.TestCase):
    def test_the_finished_text_is_emitted_once(self):
        """The loop does not stream, so on_delta gets the whole reply at the end."""
        deltas: list[str] = []
        client = ScriptedClient(
            [reply(None, [search_call("call-1")]), reply("the answer")]
        )
        run_answer_loop(client, MESSAGES, "stub", "low", on_delta=deltas.append)
        self.assertEqual(deltas, ["the answer"])


if __name__ == "__main__":
    unittest.main()
