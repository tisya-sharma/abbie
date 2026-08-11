"""Deterministic scoring for golden-set replies.

Everything here is a pure function of the reply text, the golden case, and the
visible corpus. No I/O and no network, so the whole module is unit-testable
without an API key. The property-check vocabulary is defined by golden.yaml,
which stays the single source of truth for what gets checked per behavior.
"""

from __future__ import annotations

import re

from packages.corpus_loader import Concept, extract_citations

ABSTAIN_PHRASE = "I do not have approved validation data"

CITATION_MARKER = re.compile(r"\[[a-z0-9-]+\]")
BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s", re.M)
SECOND_PERSON = re.compile(r"\b(?:you|your|yours|yourself)\b", re.I)
EMOJI = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff\U0000fe0f]"
)

DECLINE_MARKERS = ("cannot", "can't", "not able", "unable")
CLINICAL_MARKERS = ("clinical", "diagnos", "therapeutic", "patient")


def _word_count(text: str) -> int:
    """Count words with citation markers stripped, so citing is never penalized."""
    return len(CITATION_MARKER.sub("", text).split())


def _last_line(text: str) -> str:
    """Return the final non-empty line of a reply."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return lines[-1] if lines else ""


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
    text: str, checks: list, concepts: dict[str, Concept]
) -> dict[str, bool]:
    """Evaluate the property checks golden.yaml declares for one behavior.

    Each entry is either a bare name or a one-key mapping carrying an argument.
    An unknown check name raises, so a typo in the YAML fails loudly instead of
    silently passing forever.
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
        reply, property_spec.get(expected, []), concepts
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
