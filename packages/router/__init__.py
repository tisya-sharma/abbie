"""Question-intent routing for Abbie's four response behaviors.

One minimal-effort call classifies the incoming question before any generation
happens. Every failure path falls back to the answer behavior, which reproduces
the single-call full-context pipeline, so routing can never make a turn worse
than the baseline. This module predicts question intent; the post-hoc reply
classifier in packages.eval.checks measures what a reply actually did — they
are different measurements and their results are never interchangeable.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

BEHAVIORS = ("answer", "abstain", "refuse", "redirect")

ROUTE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "route",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "behavior": {"type": "string", "enum": list(BEHAVIORS)},
                "subject": {
                    "type": ["string", "null"],
                    "description": (
                        "The specific antibody, product, or dataset asked about, "
                        "verbatim from the question. Null unless behavior is abstain."
                    ),
                },
            },
            "required": ["behavior", "subject"],
            "additionalProperties": False,
        },
    },
}


@dataclass(frozen=True)
class Route:
    """Outcome of one routing call, including fallback and cost metadata."""

    behavior: str
    subject: str | None
    fallback: bool
    fallback_reason: str | None
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int


def _fallback(
    model: str,
    reason: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
) -> Route:
    """Degrade to the answer behavior, which is today's single-call pipeline."""
    return Route(
        behavior="answer",
        subject=None,
        fallback=True,
        fallback_reason=reason,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
    )


def classify(client, question: str, model: str, prompt_text: str) -> Route:
    """Classify one question into a behavior with one minimal-effort call.

    Uses strict structured output so the reply is schema-conformant JSON. On
    any API error, truncated output, unparseable content, or out-of-enum
    behavior, returns a fallback Route with behavior "answer" rather than
    raising, so a router problem degrades to the baseline instead of failing
    the turn.
    """
    from openai import OpenAIError

    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": question},
            ],
            reasoning_effort="minimal",
            max_completion_tokens=250,
            response_format=ROUTE_SCHEMA,
        )
    except OpenAIError:
        latency_ms = round((time.perf_counter() - start) * 1000)
        return _fallback(model, "api_error", 0, 0, latency_ms)

    latency_ms = round((time.perf_counter() - start) * 1000)
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    choice = response.choices[0]
    if choice.finish_reason == "length":
        return _fallback(model, "length", prompt_tokens, completion_tokens, latency_ms)

    try:
        parsed = json.loads(choice.message.content)
    except (TypeError, json.JSONDecodeError):
        return _fallback(model, "bad_json", prompt_tokens, completion_tokens, latency_ms)
    if not isinstance(parsed, dict) or parsed.get("behavior") not in BEHAVIORS:
        return _fallback(model, "bad_json", prompt_tokens, completion_tokens, latency_ms)

    behavior = parsed["behavior"]
    subject = parsed.get("subject") if behavior == "abstain" else None
    if subject is not None and not isinstance(subject, str):
        subject = None
    return Route(
        behavior=behavior,
        subject=subject,
        fallback=False,
        fallback_reason=None,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
    )
