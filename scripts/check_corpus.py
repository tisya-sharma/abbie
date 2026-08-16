"""Corpus gate checks that need no API key, for CI and for local use.

Six checks, each corresponding to a rule written down elsewhere:

- graph invariants, via the loader's own validate()
- clearance: no pre-publication concept reaches a public build
- review status, and the sign-off an approved file has to carry
- no antibody-specific identifier appears anywhere in the corpus
- no source carrying an internal label also carries a url, which is what
  would make IPI's unpublished material publishable
- every withheld source matches an internal marker, so the guardrail's list
  cannot drift out of step with the corpus without CI noticing

Deliberately not here: leak_scan. That checks text on its way to a reader,
and a corpus file is not a reader surface — its frontmatter names concept ids
in requires and leads_to, so scanning it would flag the graph itself. The
runtime scan in apps/api/main.py and the no_slug_leak eval check are where
that rule is enforced.

    python3 scripts/check_corpus.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from packages.corpus_loader import CONCEPTS_DIR, load_corpus, validate
from packages.guardrail import INTERNAL_LABEL_MARKERS

# Antibody identifiers that can be recognized by shape alone. RRIDs are the
# one format with a published, unambiguous grammar, so they are the pattern
# worth automating. Clone names and IPI design identifiers are named in the
# corpus rules too, but no regex separates them from ordinary prose without
# either missing most of them or flagging every gene symbol, so those stay
# with per-file review until someone supplies the real registry format.
CLEARANCES = frozenset({"public", "pre-publication"})

# sourced sits between draft and approved: every claim traced to a cited
# public source, but no scientist sign-off. reviewed_by belongs to approved
# alone, so a file claiming approved without one is the mistake to catch.
STATUSES = frozenset({"draft", "sourced", "approved"})

IDENTIFIER_PATTERNS = (
    ("RRID", re.compile(r"\bRRID:\s*[A-Z]{2}_\d+", re.I)),
    ("antibody registry id", re.compile(r"\bAB_\d{4,}\b")),
    ("Addgene plasmid id", re.compile(r"\bAddgene\s*#\s*\d+", re.I)),
)


def check_graph() -> list[str]:
    """Graph invariants for the public build."""
    return validate(load_corpus())


def check_clearance() -> list[str]:
    """No pre-publication concept may survive into a public build.

    The dangerous case is a misspelled clearance, not a correct one. The
    loader drops a concept only on an exact match against "pre-publication",
    so "prepublication" or "Pre-Publication" would be treated as neither
    value and ship in the public build. Asserting the vocabulary is therefore
    the check that carries the weight; confirming the filter ran is the cheap
    half that would otherwise be true by construction.
    """
    findings: list[str] = []
    every = load_corpus(include_pre_publication=True)
    for concept in every.values():
        if concept.clearance not in CLEARANCES:
            findings.append(
                f"{concept.id}: unknown clearance {concept.clearance!r}, "
                f"expected one of {sorted(CLEARANCES)}"
            )

    public = load_corpus()
    for concept_id, concept in every.items():
        if concept.clearance == "pre-publication" and concept_id in public:
            findings.append(f"{concept_id}: pre-publication reached the public build")
    return findings


def check_identifiers() -> list[str]:
    """No antibody-specific identifier anywhere in the corpus source."""
    findings: list[str] = []
    for path in sorted(CONCEPTS_DIR.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for name, pattern in IDENTIFIER_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append(
                        f"{path.name}:{line_number}: {name} {match.group(0)!r}"
                    )
    return findings


def check_internal_sources_stay_uncitable() -> list[str]:
    """An internal source must not carry a url.

    is_publishable withholds these on both conditions, so this is belt and
    braces — but the corpus is where the mistake would be made, and catching
    it here names the file rather than leaving a source silently withheld.

    Every rendered field is searched, not just the label: the widget shows
    short, journal and title too, so an internal reference parked in a title
    beside a public url would publish. The runtime scan catches that and blocks
    the whole turn, which is safe and destructive; build time is the cheaper
    place to find it.
    """
    findings: list[str] = []
    for concept in load_corpus(include_pre_publication=True).values():
        for source in concept.sources:
            if not source.get("url"):
                continue
            shown = " ".join(
                str(value) for key, value in source.items() if key != "url"
            ).lower()
            for marker in INTERNAL_LABEL_MARKERS:
                if marker in shown:
                    findings.append(
                        f"{concept.id}: internal source {marker!r} carries a url"
                    )
    return findings


def check_withheld_sources_are_marked() -> list[str]:
    """A source with no url must match an internal marker.

    This changes nothing at runtime, since is_publishable withholds a url-less
    source whatever its label says. What it buys is visibility: a label the
    markers do not recognize is invisible to leak_scan, so a reply that named
    it would reach a reader with only the prompts in the way, and the drift
    would be silent. Resolve a finding by giving the source a url, if it is
    genuinely public, or by adding its label to INTERNAL_LABEL_MARKERS.

    Paired with the check above, this is also what makes publication day
    self-checking: forget the url and this fires, forget to drop the marker
    and the other one does.
    """
    findings: list[str] = []
    for concept in load_corpus(include_pre_publication=True).values():
        for source in concept.sources:
            if source.get("url"):
                continue
            label = str(source.get("label", ""))
            if not any(m in label.lower() for m in INTERNAL_LABEL_MARKERS):
                findings.append(
                    f"{concept.id}: withheld source {label!r} matches no internal marker"
                )
    return findings


FRAMEWORK_TERMS = ("four dimensions", "four foundational dimensions", "molecular integrity",
                   "target engagement", "experimental readout")
FRAMEWORK_DRAFT = "ipi 4d framework, internal draft"


def check_framework_concepts_cite_the_draft() -> list[str]:
    """A concept stating IPI's four dimensions carries the draft label.

    This one guards a failure that would arrive silently, years from now.
    corpus/README.md tells whoever handles publication day to replace the
    internal-draft label wherever it appears, which only works if every concept
    that states the framework carries it. Six did not: the framework itself and
    its four dimensions were sourced to Deb's kickoff notes alone, so the paper
    defining them would have published and never been cited on them.

    Keyed off the prose rather than off provenance, because the risk is a new
    concept that explains the dimensions and is filed as summarized. The terms
    are deliberately specific: "selectivity" alone is an ordinary word, while
    "molecular integrity" and "target engagement" are IPI's names for things.
    """
    findings: list[str] = []
    for concept in load_corpus(include_pre_publication=True).values():
        body = concept.body.lower()
        if not any(term in body for term in FRAMEWORK_TERMS):
            continue
        labels = " ".join(str(s.get("label", "")) for s in concept.sources).lower()
        if FRAMEWORK_DRAFT not in labels:
            findings.append(
                f"{concept.id}: states IPI's dimensions but carries no draft label, "
                "so publication day would leave it behind"
            )
    return findings


def check_review_status() -> list[str]:
    """Status vocabulary, and the sign-off that approved has to carry.

    approved is the only status that asserts a scientist read the file, so it
    is the only one allowed to be claimed without reviewed_by naming who. The
    reverse is also an error: a reviewer recorded against a file still marked
    draft means one of the two fields was not updated.
    """
    findings: list[str] = []
    for concept in load_corpus(include_pre_publication=True).values():
        if concept.status not in STATUSES:
            findings.append(
                f"{concept.id}: unknown status {concept.status!r}, "
                f"expected one of {sorted(STATUSES)}"
            )
            continue
        reviewer = (concept.reviewed_by or "").strip()
        if concept.status == "approved" and not reviewer:
            findings.append(f"{concept.id}: approved but reviewed_by is empty")
        if concept.status != "approved" and reviewer:
            findings.append(
                f"{concept.id}: reviewed_by names {reviewer!r} but status is "
                f"{concept.status!r}"
            )
    return findings


CHECKS = (
    ("graph invariants", check_graph),
    ("clearance", check_clearance),
    ("review status", check_review_status),
    ("antibody identifiers", check_identifiers),
    ("internal sources uncitable", check_internal_sources_stay_uncitable),
    ("withheld sources marked", check_withheld_sources_are_marked),
    ("framework concepts cite the draft", check_framework_concepts_cite_the_draft),
)


def main() -> int:
    concepts = load_corpus()
    print(f"{len(concepts)} concepts in the public build")

    failed = False
    for name, check in CHECKS:
        findings = check()
        if findings:
            failed = True
            print(f"FAIL {name}")
            for finding in findings:
                print(f"       {finding}")
        else:
            print(f"ok   {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
