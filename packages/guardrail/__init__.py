"""Output-side guardrail for user-visible text.

The system prompt asks the model to keep corpus identifiers internal; this
module is the layer that enforces it. Everything here is a pure function of
its arguments — no I/O, no network — so the eval scorer can apply the exact
production scrub before asserting on leakage.

Two stages, used together:

- scrubbing rewrites citation-marker bracket groups before text is shown to a
  user, including the malformed multi-id and title-form groups the citation
  regexes do not recognize. Given a resolver a group becomes the ordinal of
  the source it points at; without one it is deleted outright
- leak scanning is the fail-closed backstop: it flags any corpus slug,
  internal source label, or surviving marker group in text that is about to
  reach a user surface
"""

from __future__ import annotations

import re
from typing import Callable, NamedTuple, Sequence


class CitedSources(NamedTuple):
    """What one concept contributes to a citation group.

    ``exclusive`` marks a concept whose own sources are the only ones allowed
    to stand beside it. When one is cited, the group renders its sources alone
    and drops whatever was co-cited. This module takes no view on which
    concepts earn that; it is a rule about whose evidence may sit next to
    whose, and the caller supplies the judgment.
    """

    urls: Sequence[str] = ()
    exclusive: bool = False

# Characters that appear inside citation-marker groups the model emits:
# single ids, semicolon/comma-joined id lists, and title-form groups. A group
# containing anything else is treated as literal prose and left alone.
_GROUP_INNER = re.compile(r"[a-z0-9\-;,.\s]*", re.I)

# Shape of a truncated citation marker cut off mid-stream: id tokens where
# whitespace only ever follows a separator. Prose like "[0 without close"
# fails this and is emitted rather than swallowed.
_TRUNCATED_MARKER = re.compile(r"[a-z0-9\-.]*(?:[;,]\s*[a-z0-9\-.]*)*", re.I)

# The one bracket shape allowed to reach a reader: an ordinal, or a comma-
# joined run of them, pointing into the numbered sources block. Every other
# bracket group stays a leak, so the carve-out is written as a lookahead on
# the whole inner rather than as a looser character class.
_ORDINAL_INNER = r"\d+(?:\s*,\s*\d+)*"

_MARKER_GROUP = re.compile(rf"[ \t]*\[(?!{_ORDINAL_INNER}\])[a-z0-9\-;,.\s]+\]", re.I)

# Splits a multi-id group into its ids, mirroring corpus_loader's separator.
_GROUP_SEPARATOR = re.compile(r"[;,]")

# Zero-width and joiner characters an obfuscated leak could hide behind.
_INVISIBLE = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")

# Fragments of the internal source labels, cut short enough to survive a
# paraphrase: a leaked reply says "Moshinsky's notes", not the full frontmatter
# string, and "ipi-chr" catches a sibling standard that does not exist yet.
# Every entry has to be a phrase with no legitimate use in validation prose,
# because leak_scan is fail-closed and a false positive costs a visitor their
# whole answer. That rules out "manuscript", "draft", "notes", and
# "unpublished" standing alone, since the 2016 five-pillars paper is a
# manuscript and the corpus discusses it. Those paraphrases are the prompts'
# job, not this list's. Kept here as data so the scan stays pure.
INTERNAL_LABEL_MARKERS = (
    "kickoff notes",
    "moshinsky",
    "internal draft",
    "ipi-chr",
)

# Longest bracket group still treated as a citation marker. The worst
# observed leak (a five-slug semicolon list) runs just over 100 characters,
# so the bound sits well above that while still keeping holdback finite.
MAX_GROUP_CHARS = 300


class StreamScrubber:
    """Rewrite citation-marker bracket groups in streamed text.

    Feed chunks as they arrive; each call returns text that is safe to emit.
    The scrubber holds back a partial bracket group (and the spaces before it)
    until the group either closes, stops looking like a marker, or exceeds
    MAX_GROUP_CHARS — so a literal ``[`` in prose can neither stall the stream
    nor be swallowed. One instance per reply; call flush() at end of stream.

    Without a resolver every group is deleted, which is what history scrubbing
    and the eval scorer want from it. With one, a group becomes the ordinals of
    the sources it points at and ``keys`` reports those sources in the order a
    reader met them. This is the only place that numbering is worked out: the
    numbers in the prose and the rows in the sources block have to come from
    one implementation, because a second one that drifts by a single position
    silently attributes a claim to the wrong paper. Running the same resolver
    over the same reply always yields the same numbering, so scrub_and_number
    can safely reproduce it from finished text.

    The resolver maps a concept id to a CitedSources: the keys backing it, in
    the order they should be numbered, plus whether those keys stand alone. It
    returns an empty one for a concept with no citable source, which is
    ordinary rather than exceptional: IPI's own framework grounds many answers
    and publishes no source, and those markers drop out exactly as they did
    before numbering existed.
    """

    def __init__(
        self, resolve: Callable[[str], CitedSources] | None = None
    ) -> None:
        self._buffer = ""
        self._resolve = resolve
        self._ordinals: dict[str, int] = {}
        self._exclusive_run = False

    @property
    def keys(self) -> list[str]:
        """Cited source keys in reading order; a key's ordinal is its index plus one."""
        return list(self._ordinals)

    def _render_group(self, inner: str) -> str:
        """The visible replacement for one marker group, empty to drop it."""
        if self._resolve is None:
            return ""
        resolved = [
            self._resolve(slug)
            for slug in (token.strip() for token in _GROUP_SEPARATOR.split(inner))
            if slug
        ]
        # A concept that speaks for itself does not borrow the evidence of
        # whatever was cited alongside it. A sentence stating IPI's own
        # framework picked up the five papers of a neighbor cited in the same
        # breath, which credited the wrong people for IPI's ideas.
        #
        # The run, not just this group, is what carries the rule: [a] [b] and
        # [a; b] have to behave the same way, and the model overwhelmingly
        # writes the first form because system.md asks it to. What this cannot
        # undo is a neighbor cited *before* the exclusive concept in the same
        # run, since those ordinals are already on the wire. The prompt rule
        # about citing the concept the claim actually rests on is what covers
        # that direction.
        if any(entry.exclusive for entry in resolved):
            self._exclusive_run = True
        if self._exclusive_run:
            resolved = [entry for entry in resolved if entry.exclusive]
        ordinals: list[int] = []
        for entry in resolved:
            for key in entry.urls:
                ordinal = self._ordinals.setdefault(key, len(self._ordinals) + 1)
                if ordinal not in ordinals:
                    ordinals.append(ordinal)
        if not ordinals:
            return ""
        return "[" + ", ".join(str(n) for n in ordinals) + "]"

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
            if lead:
                # Prose between two groups ends the citation run, so the next
                # group starts a fresh one. Runs matter because the model is
                # told to give each id its own brackets and does: the last run
                # produced 64 adjacent pairs against 1 combined group, so a
                # rule scoped to a single group would almost never fire.
                self._exclusive_run = False
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
                rendered = self._render_group(inner)
                if rendered:
                    out.append(spaces + rendered)
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


def scrub_and_number(
    text: str, resolve: Callable[[str], CitedSources]
) -> tuple[str, list[str]]:
    """Number a complete reply, returning visible text and its source keys.

    Chunking does not change what a scrubber produces, so running this over a
    finished reply yields exactly the text that was streamed delta by delta.
    Deriving the guarded text this way rather than accumulating what the stream
    callback happened to emit is what keeps the leak scan total: a reply
    composed without streaming still gets scanned, instead of clearing the
    backstop against an empty string.
    """
    scrubber = StreamScrubber(resolve)
    return scrubber.feed(text) + scrubber.flush(), scrubber.keys


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
