"""Per-behavior reply composition with physically separated context.

The router decides the behavior; this module decides what context that
behavior's reply is built from. refuse and abstain are deterministic text with
no model call. redirect calls the model with redirect instructions only, so no
corpus content can appear in the reply. answer is the full-context path. The
separation is the point: a path that never receives the corpus cannot cite it
or lecture from it, which is the physical-separation principle from
architecture.md applied to behaviors.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from packages.router import Route

# wording pairs with the {subject} slot in apps/api/prompts/abstain.md
DEFAULT_ABSTAIN_SUBJECT = "that antibody or product"

MAX_SUBJECT_WORDS = 12
HEADER_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.S)


def strip_header_comment(text: str) -> str:
    """Remove a leading editorial HTML comment from a prompt file's text."""
    return HEADER_COMMENT.sub("", text, count=1)


def read_prompt_file(path: str | Path) -> str:
    """Read one prompt file with its editorial header comment removed."""
    return strip_header_comment(Path(path).read_text(encoding="utf-8")).strip() + "\n"


@dataclass(frozen=True)
class ComposerPrompts:
    """Prompt texts for the four behaviors, loaded by the caller.

    answer_system is the fully assembled system prompt plus corpus from
    build_system_message. The other three never include corpus content.
    """

    answer_system: str
    redirect_system: str
    refuse_text: str
    abstain_template: str


@dataclass
class TurnResult:
    """One composed reply plus the measurements the CLI and eval need."""

    behavior: str
    text: str
    llm_called: bool
    model: str | None
    finish_reason: str | None
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int
    latency_ms: int


def _clean_subject(subject: str | None) -> str:
    """Sanitize the router's subject for insertion into the abstain template.

    Square brackets are stripped because a bracketed concept id would read as
    a citation, and overly long subjects fall back to generic wording rather
    than being truncated mid-phrase.
    """
    if not subject:
        return DEFAULT_ABSTAIN_SUBJECT
    cleaned = subject.replace("[", "").replace("]", "").replace("\n", " ").strip()
    if not cleaned or len(cleaned.split()) > MAX_SUBJECT_WORDS:
        return DEFAULT_ABSTAIN_SUBJECT
    return cleaned


def _template_result(
    behavior: str, text: str, on_delta: Callable[[str], None] | None
) -> TurnResult:
    """Wrap deterministic text in a TurnResult, emitting it once if streaming."""
    if on_delta:
        on_delta(text)
    return TurnResult(
        behavior=behavior,
        text=text,
        llm_called=False,
        model=None,
        finish_reason=None,
        prompt_tokens=0,
        completion_tokens=0,
        reasoning_tokens=0,
        latency_ms=0,
    )


def _complete(
    client,
    model: str,
    messages: list[dict],
    reasoning_effort: str,
    max_output_tokens: int | None,
    on_delta: Callable[[str], None] | None,
) -> tuple[str, str | None, int, int, int, int]:
    """One completion, streamed through on_delta when provided.

    Streaming requests ask for the trailing usage chunk, which arrives with an
    empty choices list and must not be indexed.
    """
    start = time.perf_counter()
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "reasoning_effort": reasoning_effort,
    }
    if max_output_tokens:
        kwargs["max_completion_tokens"] = max_output_tokens

    if on_delta:
        parts: list[str] = []
        finish_reason = None
        usage = None
        stream = client.chat.completions.create(
            stream=True, stream_options={"include_usage": True}, **kwargs
        )
        for chunk in stream:
            if chunk.usage:
                usage = chunk.usage
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            delta = choice.delta.content or ""
            if delta:
                parts.append(delta)
                on_delta(delta)
        text = "".join(parts)
    else:
        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        text = choice.message.content or ""
        finish_reason = choice.finish_reason
        usage = response.usage

    latency_ms = round((time.perf_counter() - start) * 1000)
    details = getattr(usage, "completion_tokens_details", None) if usage else None
    return (
        text,
        finish_reason,
        usage.prompt_tokens if usage else 0,
        usage.completion_tokens if usage else 0,
        getattr(details, "reasoning_tokens", 0) or 0,
        latency_ms,
    )


def respond(
    client,
    route: Route,
    question: str,
    prompts: ComposerPrompts,
    model: str,
    reasoning_effort: str,
    max_output_tokens: int | None = None,
    history: list[dict] | None = None,
    on_delta: Callable[[str], None] | None = None,
) -> TurnResult:
    """Dispatch one turn to the routed behavior with per-behavior context.

    refuse and abstain return deterministic text with no model call. redirect
    runs with redirect instructions only and reasoning effort pinned to
    minimal, the one place the caller's effort is ignored, since a
    two-sentence deflection gains nothing from more. answer runs the
    full-context path with conversation history at the caller's effort. When
    on_delta is provided, model paths stream deltas through it and template
    paths invoke it once with the whole text.
    """
    if route.behavior == "refuse":
        return _template_result("refuse", prompts.refuse_text, on_delta)

    if route.behavior == "abstain":
        text = prompts.abstain_template.replace(
            "{subject}", _clean_subject(route.subject)
        )
        return _template_result("abstain", text, on_delta)

    if route.behavior == "redirect":
        messages = [
            {"role": "system", "content": prompts.redirect_system},
            {"role": "user", "content": question},
        ]
        text, finish, prompt_toks, completion_toks, reasoning_toks, ms = _complete(
            client, model, messages, "minimal", max_output_tokens, on_delta
        )
        return TurnResult(
            "redirect", text, True, model, finish,
            prompt_toks, completion_toks, reasoning_toks, ms,
        )

    messages = (
        [{"role": "system", "content": prompts.answer_system}]
        + (history or [])
        + [{"role": "user", "content": question}]
    )
    text, finish, prompt_toks, completion_toks, reasoning_toks, ms = _complete(
        client, model, messages, reasoning_effort, max_output_tokens, on_delta
    )
    return TurnResult(
        "answer", text, True, model, finish,
        prompt_toks, completion_toks, reasoning_toks, ms,
    )
