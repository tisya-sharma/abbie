"""Unit tests for tracing. Run without an API key or a backend:

    python3 -m unittest packages.telemetry.test_telemetry
"""

import os
import unittest

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from packages import telemetry


class TracingTests(unittest.TestCase):
    def setUp(self):
        self.exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self._saved = telemetry._TRACER
        telemetry._TRACER = provider.get_tracer("test")

    def tearDown(self):
        telemetry._TRACER = self._saved
        os.environ.pop("ABBIE_TRACE_CONTENT", None)

    def attrs(self, name):
        for span in self.exporter.get_finished_spans():
            if span.name == name:
                return dict(span.attributes)
        self.fail(f"no span named {name}")

    def test_turn_span_carries_session_as_conversation_id(self):
        with telemetry.turn_span("sess-abc", 3):
            pass
        attrs = self.attrs("abbie.turn")
        self.assertEqual(attrs["gen_ai.conversation.id"], "sess-abc")
        self.assertEqual(attrs["abbie.turn_index"], 3)

    def test_feedback_span_records_the_verdict_as_an_evaluation_label(self):
        telemetry.record_feedback("sess-abc", 2, "down", session_live=False)
        attrs = self.attrs("abbie.feedback")
        self.assertEqual(attrs["gen_ai.conversation.id"], "sess-abc")
        self.assertEqual(attrs["abbie.turn_index"], 2)
        self.assertEqual(attrs["gen_ai.evaluation.name"], "user_feedback")
        self.assertEqual(attrs["gen_ai.evaluation.score.label"], "down")
        self.assertFalse(attrs["abbie.session_live"])

    def test_llm_span_uses_genai_convention_attributes(self):
        with telemetry.llm_span("abbie.router", "gpt-5-mini"):
            pass
        attrs = self.attrs("abbie.router")
        self.assertEqual(attrs["gen_ai.operation.name"], "chat")
        self.assertEqual(attrs["gen_ai.provider.name"], "openai")
        self.assertEqual(attrs["gen_ai.request.model"], "gpt-5-mini")

    def test_usage_and_cost_recorded(self):
        with telemetry.llm_span("abbie.composer", "gpt-5-mini") as span:
            telemetry.record_usage(span, "gpt-5-mini", 11117, 300, "stop")
        attrs = self.attrs("abbie.composer")
        self.assertEqual(attrs["gen_ai.usage.input_tokens"], 11117)
        self.assertEqual(attrs["gen_ai.usage.output_tokens"], 300)
        self.assertEqual(tuple(attrs["gen_ai.response.finish_reasons"]), ("stop",))
        # Same pricing table the eval reports from, so a production cost and an
        # eval cost for the same tokens are the same number.
        self.assertAlmostEqual(attrs[telemetry.COST_USD], 0.00169, places=6)

    def test_unknown_model_records_no_cost_rather_than_zero(self):
        with telemetry.llm_span("abbie.composer", "gpt-9-imaginary") as span:
            telemetry.record_usage(span, "gpt-9-imaginary", 100, 100)
        self.assertNotIn(telemetry.COST_USD, self.attrs("abbie.composer"))

    def test_content_withheld_by_default(self):
        with telemetry.llm_span("abbie.composer", "gpt-5-mini") as span:
            telemetry.record_content(span, "what a visitor typed", "what Abbie said")
        attrs = self.attrs("abbie.composer")
        self.assertNotIn("gen_ai.prompt", attrs)
        self.assertNotIn("gen_ai.completion", attrs)

    def test_content_captured_only_when_opted_in(self):
        os.environ["ABBIE_TRACE_CONTENT"] = "true"
        with telemetry.llm_span("abbie.composer", "gpt-5-mini") as span:
            telemetry.record_content(span, "a question", "an answer")
        attrs = self.attrs("abbie.composer")
        self.assertEqual(attrs["gen_ai.prompt"], "a question")
        self.assertEqual(attrs["gen_ai.completion"], "an answer")

    def test_spans_nest_under_the_turn(self):
        with telemetry.turn_span("sess-1", 0):
            with telemetry.llm_span("abbie.router", "gpt-5-mini"):
                pass
        spans = {s.name: s for s in self.exporter.get_finished_spans()}
        self.assertEqual(
            spans["abbie.router"].parent.span_id,
            spans["abbie.turn"].context.span_id,
        )


class BackendSelectionTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            k: os.environ.pop(k, None)
            for k in (
                "LANGFUSE_PUBLIC_KEY",
                "LANGFUSE_SECRET_KEY",
                "LANGFUSE_HOST",
                "OTEL_EXPORTER_OTLP_ENDPOINT",
            )
        }

    def tearDown(self):
        for key, value in self._saved.items():
            os.environ.pop(key, None)
            if value is not None:
                os.environ[key] = value

    def test_unconfigured_returns_none(self):
        self.assertIsNone(telemetry._otlp_settings())

    def test_langfuse_keys_produce_basic_auth_on_the_otel_path(self):
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-x"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-y"
        endpoint, headers = telemetry._otlp_settings()
        self.assertEqual(
            endpoint, telemetry.DEFAULT_LANGFUSE_HOST + telemetry.LANGFUSE_OTLP_PATH
        )
        # cGsteDpzay15 is base64 of "pk-x:sk-y"
        self.assertEqual(headers["Authorization"], "Basic cGsteDpzay15")

    def test_generic_otlp_endpoint_is_honored_without_langfuse(self):
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318/"
        endpoint, headers = telemetry._otlp_settings()
        self.assertEqual(endpoint, "http://localhost:4318/v1/traces")
        self.assertEqual(headers, {})

    def test_langfuse_wins_over_generic_endpoint(self):
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-x"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-y"
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318"
        endpoint, _ = telemetry._otlp_settings()
        self.assertIn("langfuse", endpoint)


if __name__ == "__main__":
    unittest.main()
