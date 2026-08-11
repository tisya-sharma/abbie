"""Load, validate, and assemble the concept corpus for a build target.

The corpus markdown files are the source of truth. This module reads them,
enforces the graph invariants from corpus/README.md, and renders the set of
concepts visible to a build into a single context block for the model.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONCEPTS_DIR = REPO_ROOT / "corpus" / "concepts"

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
CITATION = re.compile(r"\[([a-z0-9-]+)\]")


@dataclass
class Concept:
    id: str
    title: str
    level: str
    clearance: str
    provenance: str
    status: str
    body: str
    aliases: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    leads_to: list[str] = field(default_factory=list)


def load_corpus(include_pre_publication: bool = False) -> dict[str, "Concept"]:
    """Read every concept file and return the set visible to this build.

    Clearance filtering happens here, before anything downstream can see the
    content, which is the physical-separation rule from architecture.md.
    """
    concepts: dict[str, Concept] = {}
    for path in sorted(CONCEPTS_DIR.rglob("*.md")):
        match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            raise ValueError(f"{path.name} has no frontmatter")
        meta = yaml.safe_load(match.group(1))
        concept = Concept(
            id=meta["id"],
            title=meta["title"],
            level=meta["level"],
            clearance=meta["clearance"],
            provenance=meta["provenance"],
            status=meta.get("status", "draft"),
            body=match.group(2).strip(),
            aliases=meta.get("aliases") or [],
            sources=meta.get("sources") or [],
            requires=meta.get("requires") or [],
            leads_to=meta.get("leads_to") or [],
        )
        if concept.id != path.stem:
            raise ValueError(f"{path.name}: id {concept.id!r} does not match filename")
        if concept.clearance == "pre-publication" and not include_pre_publication:
            continue
        concepts[concept.id] = concept
    return concepts


def validate(concepts: dict[str, Concept]) -> list[str]:
    """Check the graph invariants for one build and return any violations."""
    errors: list[str] = []
    ids = set(concepts)

    order = reading_order(concepts)
    if len(order) != len(concepts):
        errors.append(f"requires graph has a cycle among {sorted(ids - set(order))}")

    for concept in concepts.values():
        if concept.level == "foundational" and concept.requires:
            errors.append(f"{concept.id}: foundational concept declares prerequisites")
        for req in concept.requires:
            if req not in ids:
                errors.append(f"{concept.id}: requires {req!r}, absent from this build")
        if concept.provenance == "summarized" and not concept.sources:
            errors.append(f"{concept.id}: summarized without sources")
        if not [t for t in concept.leads_to if t in ids]:
            errors.append(f"{concept.id}: no follow-up target resolves in this build")
    return errors


def reading_order(concepts: dict[str, Concept]) -> list[str]:
    """Topologically sort the visible concepts by their requires edges."""
    ids = set(concepts)
    indegree = {
        cid: len([r for r in concept.requires if r in ids])
        for cid, concept in concepts.items()
    }
    queue = deque(sorted(cid for cid, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for cid, concept in concepts.items():
            if current in concept.requires and cid in indegree:
                indegree[cid] -= 1
                if indegree[cid] == 0:
                    queue.append(cid)
    return order


def assemble_context(concepts: dict[str, Concept]) -> str:
    """Render the visible corpus as one delimited block, in reading order.

    Follow-up edges are filtered to targets that resolve in this build, so the
    model can never offer a concept the reader cannot reach.
    """
    ids = set(concepts)
    blocks: list[str] = []
    for cid in reading_order(concepts):
        concept = concepts[cid]
        sources = "; ".join(s.get("label", "") for s in concept.sources)
        follow_ups = ", ".join(t for t in concept.leads_to if t in ids) or "none"
        blocks.append(
            f'<concept id="{concept.id}" title="{concept.title}" '
            f'level="{concept.level}" follow_ups="{follow_ups}" '
            f'sources="{sources}">\n{concept.body}\n</concept>'
        )
    return "<corpus>\n" + "\n\n".join(blocks) + "\n</corpus>"


def extract_citations(text: str, concepts: dict[str, Concept]) -> list[str]:
    """Return concept ids the model cited, in order of first appearance."""
    seen: list[str] = []
    for cited in CITATION.findall(text):
        if cited in concepts and cited not in seen:
            seen.append(cited)
    return seen


def estimate_tokens(text: str) -> int:
    """Rough token count, close enough for budget reporting."""
    return len(text.split()) * 4 // 3
