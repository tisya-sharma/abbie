"""Output-side guardrail for user-visible text.

The system prompt asks the model to keep corpus identifiers internal; this
module is the layer that enforces it. Everything here is a pure function of
its arguments — no I/O, no network — so the eval scorer can apply the exact
production scrub before asserting on leakage.

Two stages, used together:

- scrubbing removes citation-marker bracket groups from text before it is
  shown to a user, including the malformed multi-id and title-form groups the
  citation regexes do not recognize
- leak scanning is the fail-closed backstop: it flags any corpus slug,
  internal source label, or surviving marker group in text that is about to
  reach a user surface
"""

from __future__ import annotations

import re

# Characters that appear inside citation-marker groups the model emits:
# single ids, semicolon/comma-joined id lists, and title-form groups. A group
# containing anything else is treated as literal prose and left alone.
_GROUP_INNER = re.compile(r"[a-z0-9\-;,.\s]*", re.I)

# Shape of a truncated citation marker cut off mid-stream: id tokens where
# whitespace only ever follows a separator. Prose like "[0 without close"
# fails this and is emitted rather than swallowed.
_TRUNCATED_MARKER = re.compile(r"[a-z0-9\-.]*(?:[;,]\s*[a-z0-9\-.]*)*", re.I)

_MARKER_GROUP = re.compile(r"[ \t]*\[[a-z0-9\-;,.\s]+\]", re.I)

# Zero-width and joiner characters an obfuscated leak could hide behind.
_INVISIBLE = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")

# Bibliographic labels that exist only in corpus frontmatter and must never
# appear in user-visible text. Kept here as data so the scan stays pure.
INTERNAL_LABEL_MARKERS = (
    "chatbot kickoff notes",
    "d. moshinsky",
    "ipi 4d framework, internal draft",
    "ipi-chr-001",
)

# Longest bracket group still treated as a citation marker. The worst
# observed leak (a five-slug semicolon list) runs just over 100 characters,
# so the bound sits well above that while still keeping holdback finite.
MAX_GROUP_CHARS = 300


class StreamScrubber:
    """Remove citation-marker bracket groups from streamed text.

    Feed chunks as they arrive; each call returns text that is safe to emit.
    The scrubber holds back a partial bracket group (and the spaces before it)
    until the group either closes, stops looking like a marker, or exceeds
    MAX_GROUP_CHARS — so a literal ``[`` in prose can neither stall the stream
    nor be swallowed. One instance per reply; call flush() at end of stream.
    """

    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, chunk: str) -> str:
        self._buffer += chunk
        return self._drain(final=False)

    def flush(self) -> str:
        return self._drain(final=True)

    def _drain(self, final: bool) -> str:
        out: list[str] = []
        buffer = self._buffer
        while buffer:
            start = buffer.find("[")
            if start == -1:
                if final:
                    out.append(buffer)
                    buffer = ""
                    break
                # Trailing spaces might precede a bracket in the next chunk,
                # hold them so a dropped group also drops its leading gap.
                keep = len(buffer)
                while keep > 0 and buffer[keep - 1] in " \t":
                    keep -= 1
                out.append(buffer[:keep])
                buffer = buffer[keep:]
                break

            lead = start
            while lead > 0 and buffer[lead - 1] in " \t":
                lead -= 1
            out.append(buffer[:lead])
            spaces = buffer[lead:start]
            rest = buffer[start:]
            close = rest.find("]")

            if close == -1:
                inner = rest[1:]
                may_become_marker = (
                    _GROUP_INNER.fullmatch(inner) is not None
                    and len(inner) <= MAX_GROUP_CHARS
                )
                if may_become_marker and not final:
                    buffer = spaces + rest
                    break
                if final and _TRUNCATED_MARKER.fullmatch(inner):
                    # Marker cut off at end of reply, drop rather than leak.
                    buffer = ""
                    break
                # Literal bracket, emit it and keep scanning after it.
                out.append(spaces + "[")
                buffer = rest[1:]
                continue

            inner = rest[1:close]
            if (
                _GROUP_INNER.fullmatch(inner)
                and inner.strip()
                and len(inner) <= MAX_GROUP_CHARS
            ):
                buffer = rest[close + 1 :]
                continue
            out.append(spaces + rest[: close + 1])
            buffer = rest[close + 1 :]

        self._buffer = buffer
        return "".join(out)


def scrub_text(text: str) -> str:
    """Remove citation-marker bracket groups from a complete text."""
    scrubber = StreamScrubber()
    return scrubber.feed(text) + scrubber.flush()


def is_publishable(source: dict) -> bool:
    """Whether a frontmatter source may be shown to a reader.

    Two independent conditions, both required. A public URL is what makes a
    source citable at all. The internal-label check is the deliberate half:
    IPI's unpublished material grounds answers but is never itself cited, and
    leaning on the absent URL alone would publish it the day someone adds one.

    Every surface that renders a source calls this — the widget's sources row
    and the exported checklist's reference list alike. One rule in one place,
    because a surface that reimplements half of it drifts silently.
    """
    if not source.get("url"):
        return False
    label = str(source.get("label", "")).lower()
    return not any(marker in label for marker in INTERNAL_LABEL_MARKERS)


def _normalize(text: str) -> str:
    return _INVISIBLE.sub("", text).lower()


def _slug_used_as_identifier(slug: str, normalized: str) -> bool:
    """Whether a slug appears as an identifier rather than natural prose.

    English hyphenates a two-word compound modifier before a noun — "IPI's
    antibody-validation expertise" is ordinary prose, not a file name. So a
    single-hyphen slug is flagged only when the next thing after it is not a
    following word: end of text, punctuation, or a separator, which is how
    identifiers and enumerations actually terminate. A slug with two or more
    hyphens never occurs as natural English (a writer breaks the compound at
    the noun: "four-dimensional framework"), so it flags anywhere.
    """
    boundary = rf"(?<![a-z0-9]){re.escape(slug)}(?![a-z0-9-])"
    if slug.count("-") >= 2:
        return re.search(boundary, normalized) is not None
    return re.search(boundary + r"(?![ \t][a-z])", normalized) is not None


def leak_scan(text: str, slugs: list[str] | set[str]) -> list[str]:
    """Return the leaks found in text destined for a user surface.

    Matches, on normalized text: surviving marker-shaped bracket groups,
    hyphenated corpus slugs used as identifiers, and internal source-label
    phrases. Single-word slugs are excluded on purpose — a bare word like
    "selectivity" is legitimate prose, and the policy protects file names,
    which are all hyphenated. An empty return means the text is clean.
    """
    normalized = _normalize(text)
    findings: list[str] = []
    if _MARKER_GROUP.search(normalized):
        findings.append("bracket-marker group")
    for slug in sorted(slugs):
        if "-" in slug and _slug_used_as_identifier(slug, normalized):
            findings.append(f"slug: {slug}")
    for label in INTERNAL_LABEL_MARKERS:
        if label in normalized:
            findings.append(f"internal label: {label}")
    return findings
