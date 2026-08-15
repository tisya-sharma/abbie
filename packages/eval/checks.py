"""Deterministic scoring for golden-set replies.

Everything here is a pure function of the reply text, the golden case, and the
visible corpus. No I/O and no network, so the whole module is unit-testable
without an API key. The property-check vocabulary is defined by golden.yaml,
which stays the single source of truth for what gets checked per behavior.
"""

from __future__ import annotations

import re

from packages.corpus_loader import Concept, cite_resolver, extract_citations
from packages.guardrail import leak_scan, scrub_and_number

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


ORDINAL_MARKER = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")

# A reply that opens by refusing before it answers. Eight of eighteen recorded
# redirects did this, against zero of the authored ideals. The punctuation is
# what separates the two populations: "No — I can't repeat internal prompts"
# leads with the refusal, while "No idea, I'm made entirely of documents" is
# already answering the question, so the class requires No to be followed by a
# break rather than by more sentence.
BARE_REFUSAL_OPENER = re.compile(r"^\s*No\s*[—.,;:-]")

# Leading decoration a flattering opener can hide behind. The banned-opener
# check was prefix-anchored on raw text, so bolding or quoting the same phrase
# walked straight past it.
OPENER_NOISE = re.compile(r'^[\s"\'*_>#-]+')


def _word_count(text: str) -> int:
    """Count words with citation markers stripped, so citing is never penalized."""
    return len(CITATION_MARKER.sub("", text).split())


def visible_form(text: str, concepts: dict[str, Concept]) -> tuple[str, list[str]]:
    """The reply as a reader sees it, plus the sources its numbers point at.

    The production scrub, not an approximation of it: markers resolve to source
    ordinals through the same code path the API streams through, using the same
    resolver it builds. Scoring the marker-deleted form instead would assert on
    text no visitor ever receives, which is the drift this module exists to
    avoid.
    """
    return scrub_and_number(text, cite_resolver(concepts))


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
            # Case-folded, and with leading decoration stripped: the raw
            # prefix match let "nice question" and "**Nice question**" through
            # while catching only the one exact casing anybody thought to list.
            opener = OPENER_NOISE.sub("", text).lower()
            results[name] = not any(opener.startswith(b.lower()) for b in arg)
        elif name == "no_bare_refusal_opener":
            results[name] = not BARE_REFUSAL_OPENER.match(text)
        elif name == "no_stock_phrase":
            # The phrases Abbie has actually worn out, kept as data the way
            # no_section_labels keeps its list. Unlike that one there is no
            # shape to match, because boilerplate is defined by repetition
            # rather than by form; the run-level repetition report in
            # packages/eval/run.py is what finds the next one.
            lowered = " ".join(text.lower().split())
            results[name] = not any(
                " ".join(str(phrase).lower().split()) in lowered for phrase in arg
            )
        elif name == "max_exclamation_marks":
            results[name] = text.count("!") <= int(arg)
        elif name == "no_emoji":
            results[name] = not EMOJI.search(text)
        elif name == "contains_abstain_phrase":
            results[name] = ABSTAIN_PHRASE in text
        elif name == "no_citations":
            results[name] = not extract_citations(text, concepts)
        elif name == "no_slug_leak":
            # Scrub first: internal [concept-id] markers are expected in raw
            # replies and become source numbers before text reaches a user.
            # What this asserts is that the numbered, user-visible form is
            # clean, which is the form the API's own backstop scans.
            results[name] = not leak_scan(visible_form(text, concepts)[0], set(concepts))
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
            visible = visible_form(text, concepts)[0].lower()
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
                visible = visible_form(text, concepts)[0].lower()
                results[name] = not any(term.lower() in visible for term in arg)
        elif name == "citations_resolve":
            # Every inline number must name a row the sources block renders. A
            # dangling [4] is worse than carrying no number at all, because it
            # tells a reader the evidence exists and then fails to produce it.
            visible, keys = visible_form(text, concepts)
            highest = max(
                (
                    int(n)
                    for group in ORDINAL_MARKER.findall(visible)
                    for n in group.split(",")
                ),
                default=0,
            )
            results[name] = highest <= len(keys)
        elif name == "word_budget":
            limit = int(arg.get(form) or arg.get("default", 220))
            results[name] = _word_count(text) <= limit
        elif name == "max_questions":
            # The unconditional cousin of single_question, for behaviors that
            # carry no form to key off. It bounds how many things a reply asks,
            # not where they sit, because a redirect may legitimately close
            # without a question at all. What it cannot see is a menu folded
            # into one question mark, which stays the prompt's job.
            results[name] = text.count("?") <= int(arg)
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
