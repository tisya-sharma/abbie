"""Deterministic scoring for golden-set replies.

Everything here is a pure function of the reply text, the golden case, and the
visible corpus. No I/O and no network, so the whole module is unit-testable
without an API key. The property-check vocabulary is defined by golden.yaml,
which stays the single source of truth for what gets checked per behavior.
"""

from __future__ import annotations

import re

from packages.corpus_loader import Concept, extract_citations
from packages.guardrail import leak_scan, scrub_text

ABSTAIN_PHRASE = "I do not have approved validation data"

# Matches whole marker groups, including separator-joined ones like [a; b],
# mirroring the citation regex in corpus_loader and the production scrubber.
CITATION_MARKER = re.compile(r"\[[a-z0-9\-;,.\s]+\]", re.I)
BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s", re.M)
SECOND_PERSON = re.compile(r"\b(?:you|your|yours|yourself)\b", re.I)
EMOJI = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff\U0000fe0f]"
)

DECLINE_MARKERS = ("cannot", "can't", "not able", "unable")
CLINICAL_MARKERS = ("clinical", "diagnos", "therapeutic", "patient")

# A labeled section is a line that opens with a short capitalized fragment and
# a colon. Matching the shape rather than the wording is deliberate: the
# earlier denylist enumerated the nine labels seen during one tuning pass, and
# the model simply invented new ones ("Short answer:", "Positive controls:"),
# so every observed violation scored as a pass.
#
# Four words is where the two populations separate. Real labels are noun
# fragments and stay short ("Why:", "Positive controls:", "Orthogonal or
# expression controls:"). Line-initial prose colons carry a finite verb and run
# longer ("The dimensions are ordered by dependency:"), so the length cap
# stands in for a clause test that would otherwise need a parser.
LABEL_LINE = re.compile(r"^\s{0,3}[A-Z][^:\n]{0,60}:\s", re.M)
MAX_LABEL_WORDS = 4

EM_DASH = "—"
BOLD_SPAN = re.compile(r"\*\*[^*\n]+\*\*")


def _word_count(text: str) -> int:
    """Count words with citation markers stripped, so citing is never penalized."""
    return len(CITATION_MARKER.sub("", text).split())


def _last_line(text: str) -> str:
    """Return the final non-empty line of a reply."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return lines[-1] if lines else ""


def section_labels(text: str) -> list[str]:
    """Every line-initial "Label:" fragment in a reply, shortest form first.

    Returned rather than counted so a failure names what it caught, which is
    what makes a new label worth adding to the documented list in golden.yaml.
    """
    found = []
    for match in LABEL_LINE.finditer(CITATION_MARKER.sub("", text)):
        label = match.group().strip().rstrip(":").strip()
        if label and len(label.split()) <= MAX_LABEL_WORDS:
            found.append(label)
    return found


def classify_behavior(text: str, concepts: dict[str, Concept]) -> str:
    """Assign a reply to one of the four behaviors from the system prompt.

    Abstention is deterministic because the prompt pins its opening words.
    Refuse detection is a keyword heuristic, a known softness that stays
    visible in the per-case report rather than being hidden. This scores reply
    text after the fact; packages.router.classify predicts question intent
    before generation — different measurements, never interchangeable.
    """
    if ABSTAIN_PHRASE in text:
        return "abstain"
    lowered = text.lower()
    if any(d in lowered for d in DECLINE_MARKERS) and any(
        c in lowered for c in CLINICAL_MARKERS
    ):
        return "refuse"
    if extract_citations(text, concepts):
        return "answer"
    return "redirect"


def run_property_checks(
    text: str,
    checks: list,
    concepts: dict[str, Concept],
    question: str = "",
    form: str | None = None,
) -> dict[str, bool]:
    """Evaluate the property checks golden.yaml declares for one behavior.

    Each entry is either a bare name or a one-key mapping carrying an argument.
    An unknown check name raises, so a typo in the YAML fails loudly instead of
    silently passing forever. The question is passed so mention checks can
    exempt replies to questions that themselves raise the term; form is the
    case's authored question-form tag, which shape checks key off — never the
    router's runtime prediction, so scoring stays deterministic.
    """
    results: dict[str, bool] = {}
    for entry in checks:
        if isinstance(entry, dict):
            name, arg = next(iter(entry.items()))
        else:
            name, arg = entry, None
        if name == "ends_with_followup":
            closing = CITATION_MARKER.sub("", _last_line(text)).rstrip()
            results[name] = closing.endswith("?")
        elif name == "uses_second_person":
            results[name] = bool(SECOND_PERSON.search(text))
        elif name == "max_words":
            results[name] = _word_count(text) <= int(arg)
        elif name == "max_bullets":
            results[name] = len(BULLET.findall(text)) <= int(arg)
        elif name == "no_banned_openers":
            opener = text.lstrip()
            results[name] = not any(opener.startswith(b) for b in arg)
        elif name == "no_exclamation_marks":
            results[name] = "!" not in text
        elif name == "no_emoji":
            results[name] = not EMOJI.search(text)
        elif name == "contains_abstain_phrase":
            results[name] = ABSTAIN_PHRASE in text
        elif name == "no_citations":
            results[name] = not extract_citations(text, concepts)
        elif name == "no_slug_leak":
            # Scrub first: internal [concept-id] markers are expected in raw
            # replies and are removed before text ever reaches a user. What
            # this asserts is that the scrubbed, user-visible form is clean.
            results[name] = not leak_scan(scrub_text(text), set(concepts))
        elif name == "no_section_labels":
            # arg is the list of labels already caught in the wild, kept as
            # documentation. The structural match is what catches the ones
            # nobody has invented yet, which is every one observed so far.
            lines = [line.lstrip() for line in text.splitlines()]
            known = any(line.startswith(label) for line in lines for label in arg)
            results[name] = not known and not section_labels(text)
        elif name == "no_artifact_offers":
            # Abbie can teach a topic; she cannot hand over a file. Offering
            # one is a promise with no fulfillment path, so the terms are
            # barred outright rather than only in the closing sentence.
            visible = scrub_text(text).lower()
            results[name] = not any(
                re.search(rf"\b{re.escape(str(term).lower())}\b", visible)
                for term in arg
            )
        elif name == "max_em_dashes":
            results[name] = text.count(EM_DASH) <= int(arg)
        elif name == "max_bold_spans":
            results[name] = len(BOLD_SPAN.findall(text)) <= int(arg)
        elif name == "word_floor":
            # Guards the direction word_budget cannot: a procedural reply that
            # collapses back to an orientation stub withholding the process.
            floor = arg.get(form) if isinstance(arg, dict) else None
            results[name] = floor is None or _word_count(text) >= int(floor)
        elif name == "no_unprompted_mention":
            if any(term.lower() in question.lower() for term in arg):
                results[name] = True
            else:
                visible = scrub_text(text).lower()
                results[name] = not any(term.lower() in visible for term in arg)
        elif name == "word_budget":
            limit = int(arg.get(form) or arg.get("default", 220))
            results[name] = _word_count(text) <= limit
        elif name == "single_question":
            # Applies only to the forms the arg lists. Real replies carry one
            # rhetorical mid-text question at most, so the bound is: at most
            # two question marks overall, and the closing line asks exactly
            # one. Slot-compounding inside a single question is bounded by
            # the form's word budget instead.
            if form not in arg:
                results[name] = True
            else:
                closing = CITATION_MARKER.sub("", _last_line(text)).rstrip()
                results[name] = (
                    text.count("?") <= 2
                    and closing.endswith("?")
                    and closing.count("?") == 1
                )
        else:
            raise ValueError(f"unknown property check: {name}")
    return results


def score_case(
    case: dict,
    reply: str,
    concepts: dict[str, Concept],
    property_spec: dict[str, list],
) -> dict:
    """Score one reply against its golden case, returning named checks.

    Behavior and citations are always checked. must_cite applies only to
    answer cases, and the per-behavior property checks come from golden.yaml.
    The judge field is a seam for a later model-graded pass against the ideal.
    """
    expected = case["behavior"]
    observed = classify_behavior(reply, concepts)
    citations = extract_citations(reply, concepts)

    checks: dict[str, bool] = {"behavior": observed == expected}
    failures: list[str] = []
    if not checks["behavior"]:
        failures.append(f"behavior: expected {expected}, observed {observed}")

    if expected == "answer":
        required = set(case.get("must_cite", []))
        checks["must_cite"] = required <= set(citations)
        if not checks["must_cite"]:
            missing = ", ".join(sorted(required - set(citations)))
            failures.append(f"must_cite: missing {missing}")

    for name, passed in run_property_checks(
        reply,
        property_spec.get(expected, []),
        concepts,
        case.get("question", ""),
        case.get("form"),
    ).items():
        checks[name] = passed
        if not passed:
            failures.append(name)

    return {
        "id": case["id"],
        "behavior_expected": expected,
        "behavior_observed": observed,
        "citations": citations,
        "checks": checks,
        "failures": failures,
        "passed": not failures,
        "judge": None,
    }
