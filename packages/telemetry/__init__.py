"""OpenTelemetry tracing for the answer pipeline.

Instrumented against the OpenTelemetry GenAI semantic conventions rather than a
vendor SDK, so the backend is an environment variable rather than a rewrite.
Those conventions are still pre-stable: the gen_ai.* attributes moved to their
own repository at semconv 1.42 and carry no stabilization date, so the
attribute names are read from the installed package rather than hardcoded, and
the package version is pinned in pyproject.

Telemetry is optional at runtime. With no exporter configured the OTel API's
own no-op tracer is used, which means the demo runs unchanged on a laptop with
no account, no keys, and no network calls. Nothing in the request path branches
on whether tracing is on.

Content capture is off by default. Prompts and replies carry whatever a visitor
typed, so recording them is a storage decision about personal data rather than
a debugging convenience, and it is opted into explicitly.
"""

from __future__ import annotations

import base64
import os
from contextlib import contextmanager
from typing import Iterator

from opentelemetry import trace
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes as gen_ai

from packages.pricing import estimate_cost

LANGFUSE_OTLP_PATH = "/api/public/otel/v1/traces"
DEFAULT_LANGFUSE_HOST = "https://cloud.langfuse.com"

# Not a GenAI convention attribute: cost is derived from the pinned pricing
# table rather than reported by the provider, so it is namespaced to this
# application to keep it distinguishable from anything the spec later defines.
COST_USD = "abbie.cost_usd"

_TRACER: trace.Tracer | None = None
_PROVIDER = None


def content_capture_enabled() -> bool:
    """Whether prompt and completion text may be attached to spans."""
    return os.environ.get("ABBIE_TRACE_CONTENT", "").lower() in {"1", "true", "yes"}


def _otlp_settings() -> tuple[str, dict[str, str]] | None:
    """Endpoint and headers for the configured backend, or None if unconfigured.

    Langfuse is configured with its own key pair and authenticates with Basic
    auth over OTLP/HTTP; it does not accept gRPC. A generic OTLP endpoint is
    honored too, so pointing at Phoenix or a collector needs no code change.
    """
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    if public_key and secret_key:
        host = os.environ.get("LANGFUSE_HOST", DEFAULT_LANGFUSE_HOST).rstrip("/")
        token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        return host + LANGFUSE_OTLP_PATH, {"Authorization": f"Basic {token}"}

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        return endpoint.rstrip("/") + "/v1/traces", {}
    return None


def configure(service_name: str = "abbie") -> bool:
    """Install the tracer provider. Returns whether an exporter was configured.

    Safe to call more than once and safe to call with nothing configured, in
    which case spans are created against the API's no-op tracer and discarded.
    """
    global _TRACER, _PROVIDER
    if _TRACER is not None:
        return _PROVIDER is not None

    settings = _otlp_settings()
    if settings is None:
        _TRACER = trace.get_tracer(service_name)
        return False

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    endpoint, headers = settings
    provider = TracerProvider(
        resource=Resource.create({"service.name": service_name})
    )
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers))
    )
    trace.set_tracer_provider(provider)
    _PROVIDER = provider
    _TRACER = trace.get_tracer(service_name)
    return True


def _tracer() -> trace.Tracer:
    if _TRACER is None:
        configure()
    assert _TRACER is not None
    return _TRACER


def shutdown() -> None:
    """Flush pending spans. Call on application shutdown or spans are lost."""
    if _PROVIDER is not None:
        _PROVIDER.shutdown()


@contextmanager
def turn_span(session_id: str, turn_index: int) -> Iterator[trace.Span]:
    """Root span for one conversational turn.

    The session id becomes the GenAI conversation id, which is what groups a
    multi-turn conversation into a single reviewable object downstream.
    """
    with _tracer().start_as_current_span("abbie.turn") as span:
        span.set_attribute(gen_ai.GEN_AI_CONVERSATION_ID, session_id)
        span.set_attribute("abbie.turn_index", turn_index)
        yield span


@contextmanager
def llm_span(name: str, model: str) -> Iterator[trace.Span]:
    """Span for one model call, carrying the request-side GenAI attributes."""
    with _tracer().start_as_current_span(name) as span:
        span.set_attribute(
            gen_ai.GEN_AI_OPERATION_NAME, gen_ai.GenAiOperationNameValues.CHAT.value
        )
        span.set_attribute(gen_ai.GEN_AI_PROVIDER_NAME, "openai")
        span.set_attribute(gen_ai.GEN_AI_REQUEST_MODEL, model)
        yield span


@contextmanager
def tool_span(name: str, tool_name: str, call_id: str) -> Iterator[trace.Span]:
    """Span for one tool execution inside the bounded loop.

    A loop turn spends an unknown number of calls, so per-call spans are what
    keep its cost and latency readable rather than arriving as one opaque
    total. The call id is carried so a span can be matched to the request that
    produced it when a model asks for several tools at once.

    Arguments and results are deliberately not attached. They can carry
    whatever a visitor typed, and adding them is the same storage decision that
    content capture already exists to make explicitly.
    """
    with _tracer().start_as_current_span(name) as span:
        span.set_attribute(
            gen_ai.GEN_AI_OPERATION_NAME,
            gen_ai.GenAiOperationNameValues.EXECUTE_TOOL.value,
        )
        span.set_attribute(gen_ai.GEN_AI_TOOL_NAME, tool_name)
        span.set_attribute(gen_ai.GEN_AI_TOOL_CALL_ID, call_id)
        yield span


@contextmanager
def step_span(name: str) -> Iterator[trace.Span]:
    """Span for a non-model pipeline step, such as the guardrail scan."""
    with _tracer().start_as_current_span(name) as span:
        yield span


def record_feedback(
    session_id: str, turn_index: int, verdict: str, session_live: bool
) -> None:
    """Emit the span for one thumbs verdict on an answered turn.

    A standalone span rather than a context manager, because a verdict is a
    point event that arrives long after its turn's span closed and has no work
    nested under it. The GenAI conventions model a judgment about a reply as an
    evaluation, so the verdict travels as a score label rather than a value: a
    thumb has no scale behind it to report a number from.

    session_live records whether the server still held the session when the
    verdict arrived, so a trace does not read as though the turn was found when
    it was not.
    """
    with _tracer().start_as_current_span("abbie.feedback") as span:
        span.set_attribute(gen_ai.GEN_AI_CONVERSATION_ID, session_id)
        span.set_attribute("abbie.turn_index", turn_index)
        span.set_attribute(gen_ai.GEN_AI_EVALUATION_NAME, "user_feedback")
        span.set_attribute(gen_ai.GEN_AI_EVALUATION_SCORE_LABEL, verdict)
        span.set_attribute("abbie.session_live", session_live)


def record_usage(
    span: trace.Span,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    finish_reason: str | None = None,
) -> None:
    """Attach response-side usage and the derived cost to a model-call span."""
    span.set_attribute(gen_ai.GEN_AI_RESPONSE_MODEL, model)
    span.set_attribute(gen_ai.GEN_AI_USAGE_INPUT_TOKENS, prompt_tokens)
    span.set_attribute(gen_ai.GEN_AI_USAGE_OUTPUT_TOKENS, completion_tokens)
    if finish_reason:
        span.set_attribute(gen_ai.GEN_AI_RESPONSE_FINISH_REASONS, [finish_reason])
    cost = estimate_cost(model, prompt_tokens, completion_tokens)
    if cost is not None:
        span.set_attribute(COST_USD, cost)


def record_content(span: trace.Span, prompt: str | None, completion: str | None) -> None:
    """Attach prompt and completion text, when content capture is enabled.

    Silently does nothing otherwise. The caller should not have to check first,
    because a caller that forgets the check is how transcripts end up somewhere
    nobody decided to put them.
    """
    if not content_capture_enabled():
        return
    if prompt is not None:
        span.set_attribute(gen_ai.GEN_AI_PROMPT, prompt)
    if completion is not None:
        span.set_attribute(gen_ai.GEN_AI_COMPLETION, completion)
