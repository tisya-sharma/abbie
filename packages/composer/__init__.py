"""Per-behavior reply composition with physically separated context.

The router decides the behavior; this module decides what context that
behavior's reply is built from. refuse and abstain are deterministic text with
no model call. redirect calls the model with redirect instructions only, so no
corpus content can appear in the reply. answer is the full-context path. The
separation is the point: a path that never receives the corpus cannot cite it
or lecture from it, which is the physical-separation principle applied to
behaviors.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from packages.guardrail import leak_scan, scrub_text
from packages.router import Route

# wording pairs with the {subject} slot in apps/api/prompts/abstain.md
DEFAULT_ABSTAIN_SUBJECT = "that antibody or product"

MAX_SUBJECT_WORDS = 12

# Words that mark a subject as a document rather than a reagent. The abstain
# template is the one path that copies a visitor's own words into a visible
# reply with no model in between, so "send me the antibody QC standard" routed
# here on the word antibody would print the artifact's name back and confirm it
# exists. A false positive costs only the generic wording, which is why a
# denylist is acceptable here and is not in leak_scan, where a false positive
# costs a visitor their whole answer.
ARTIFACT_WORDS = frozenset(
    {
        "manuscript", "draft", "preprint", "notes", "memo", "sop",
        "standard", "document", "file", "paper", "protocol",
    }
)
WORD = re.compile(r"[a-z]+")
HEADER_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.S)

# One exchange is enough to resolve a pronoun in a follow-up redirect and short
# enough that the redirect path stays close to context-free.
REDIRECT_CONTEXT_TURNS = 2


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
    than being truncated mid-phrase. A subject naming a document falls back
    too: no model sees this text, so nothing downstream would catch it.
    Matching on whole words is what keeps "standardize" from tripping
    "standard", and the empty slug set makes leak_scan a marker-only check,
    which catches an internal identifier without a second copy of that list.
    """
    if not subject:
        return DEFAULT_ABSTAIN_SUBJECT
    cleaned = subject.replace("[", "").replace("]", "").replace("\n", " ").strip()
    if not cleaned or len(cleaned.split()) > MAX_SUBJECT_WORDS:
        return DEFAULT_ABSTAIN_SUBJECT
    if leak_scan(cleaned, set()) or ARTIFACT_WORDS.intersection(
        WORD.findall(cleaned.lower())
    ):
        return DEFAULT_ABSTAIN_SUBJECT
    return cleaned


def _redirect_context(history: list[dict] | None) -> list[dict]:
    """The last exchange only, with assistant text scrubbed of citation markers.

    An off-topic follow-up like "do you have a resource for that?" is a
    non-sequitur without the turn it refers to, so the redirect path gets one
    exchange rather than nothing. It stays one exchange because this path is
    the corpus-free one and every message added to it widens what an injection
    carried in history could reach. Scrubbing matters for the same reason the
    answer path scrubs on the way out: history holds raw replies, and a marker
    echoed here would be a leak from a path that is supposed to have no corpus
    to leak.
    """
    if not history:
        return []
    recent = history[-REDIRECT_CONTEXT_TURNS:]
    return [
        {
            "role": message["role"],
            "content": (
                scrub_text(message["content"])
                if message["role"] == "assistant"
                else message["content"]
            ),
        }
        for message in recent
        if message.get("content")
    ]


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


SHAPE_HINTS = {
    "definitional": (
        "Shape this reply as a definition: about 110 words. Say what the thing"
        " is and why it matters, one concrete image, then the closing question."
    ),
    "conceptual": (
        "Shape this reply as an explanation: about 150 words. One idea developed"
        " properly, its boundary, then the closing question."
    ),
    "comparative": (
        "Shape this reply as a comparison: about 150 words. Contrast on the two"
        " or three criteria that actually separate the things, then the closing"
        " question."
    ),
    "procedural": (
        "Shape this reply as a procedural answer: about 150 words, and the"
        " process is in this reply. Give the three or four moves that matter,"
        " in the order they happen, carried by ordinary connectives rather"
        " than a numbered list. Where the question left something open, name"
        " the assumption you took instead of asking first, and say in one"
        " clause where your knowledge stops. Close with a single question"
        " about the one decision that determines their next move."
    ),
    "deepening": (
        "The user asked for depth. The full picture is welcome, up to the"
        " 200-word ceiling; still end with a door."
    ),
    "acceptance": (
        "The user is responding to the question that closed your last reply."
        " If that question offered a topic, deliver it in full. If it asked"
        " about their situation, treat their answer as the fact it gives you"
        " and give the guidance it unlocks, rather than restating the general"
        " case. Either way, up to the 200-word ceiling, never repeat what you"
        " already covered, and still end with a door."
    ),
}

# Prerequisite expansion, and the whole of it. Under a full-context baseline the
# prerequisite is already in the prompt, so this cannot mean pulling anything in:
# it is an instruction with a resolvable referent, which is what the requires
# attribute on each concept block supplies.
#
# Gated to definitional because that is the form that reads as foundational. A
# scientist asking how to rank antibodies for IHC does not want paralog defined
# at them, and widening this would undo the reason the split exists.
#
# The one-clause bound is load-bearing rather than stylistic. Definitional replies
# are scored against a 180-word cap and already land near it, so a gloss that
# spends a sentence would push passing cases over.
GLOSS_FORMS = frozenset({"definitional"})

PREREQUISITE_HINT = (
    " The reader is meeting this cold. Each concept block names what it depends"
    " on in its requires attribute; where one of those is something this answer"
    " leans on and the conversation has not covered it already, define it in a"
    " handful of words inside the clause that first uses it, and cite it as you"
    " would anything else you drew on. At most one, never a sentence of its own,"
    " and never at the cost of the length above."
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
    runs with redirect instructions and the last exchange only, never the
    corpus, so it cannot cite or lecture from it. answer runs the full-context
    path with conversation history. Both model paths use the caller's reasoning
    effort: a redirect is two sentences, but landing warmth and wit in two
    sentences is not the cheap problem it looks like, and pinning that path to
    minimal is what made every deflection read from the same template. When
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
        messages = (
            [{"role": "system", "content": prompts.redirect_system}]
            + _redirect_context(history)
            + [{"role": "user", "content": question}]
        )
        text, finish, prompt_toks, completion_toks, reasoning_toks, ms = _complete(
            client, model, messages, reasoning_effort, max_output_tokens, on_delta
        )
        return TurnResult(
            "redirect", text, True, model, finish,
            prompt_toks, completion_toks, reasoning_toks, ms,
        )

    # The shape hint is per-turn steering from the router's form prediction.
    # It sits after history so it never enters what later turns replay, and a
    # missing or unrecognized form simply omits it, reproducing the default
    # shape from the system prompt.
    shape_hint = SHAPE_HINTS.get(route.form) if route.form else None
    if shape_hint and route.form in GLOSS_FORMS:
        shape_hint += PREREQUISITE_HINT
    messages = (
        [{"role": "system", "content": prompts.answer_system}]
        + (history or [])
        + ([{"role": "system", "content": shape_hint}] if shape_hint else [])
        + [{"role": "user", "content": question}]
    )
    text, finish, prompt_toks, completion_toks, reasoning_toks, ms = _complete(
        client, model, messages, reasoning_effort, max_output_tokens, on_delta
    )
    return TurnResult(
        "answer", text, True, model, finish,
        prompt_toks, completion_toks, reasoning_toks, ms,
    )
