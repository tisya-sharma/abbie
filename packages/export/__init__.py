"""Deterministic checklist documents composed from corpus frontmatter.

The model never authors an exported document. It chooses which concepts an
answer drew on, and this module lays those concepts' `checklist` entries into a
fixed template, so what a visitor prints is reviewed once here rather than
regenerated in prose on every request. Same concepts in, same bytes out, apart
from the date stamp the caller supplies.

Layout follows the widget's tokens where a PDF can: the same greys, the same
ordering, checkbox items with the claim each one supports underneath. Type is
Helvetica rather than Hanken Grotesk because the core fonts need no embedded
file and the repo ships none.
"""

from __future__ import annotations

from dataclasses import dataclass

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from packages.corpus_loader import Concept
from packages.guardrail import is_publishable

# Fixed rather than derived from the concepts in the document: a filename
# built from concept ids would carry them out of the server in the
# Content-Disposition header, which is the one thing no user surface may do.
CHECKLIST_FILENAME = "abbie-validation-checklist.pdf"

DISPLAY = (27, 30, 35)
BODY = (75, 80, 88)
MUTED = (110, 115, 123)
LINE = (198, 203, 210)

PAGE_MARGIN = 18
BOX = 3.4

# The document says what it is not, in the document, because a checklist that
# travels away from Abbie loses the conversation that framed it.
SCOPE_NOTE = (
    "This lists the evidence that makes a result attributable. It is not a "
    "protocol: it does not give volumes, times, dilutions, or instrument "
    "settings, and it does not replace validation for your own sample and "
    "application."
)


@dataclass(frozen=True)
class ChecklistDocument:
    """One rendered checklist, ready to serve."""

    filename: str
    body: bytes


def _latin1(text: str) -> str:
    """Fold text into what the core fonts can encode, losing nothing readable."""
    replacements = {"—": "-", "–": "-", "‘": "'", "’": "'",
                    "“": '"', "”": '"', "…": "..."}
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")


def checklist_concepts(
    concepts: dict[str, Concept], concept_ids: list[str]
) -> list[Concept]:
    """The cited concepts that actually carry a checklist, in corpus order.

    Ordering comes from the corpus rather than from the citation order in a
    reply, so the same set of concepts always prints the same way regardless of
    the sentence order the model happened to produce.
    """
    wanted = set(concept_ids)
    return [c for cid, c in concepts.items() if cid in wanted and c.checklist]


def _flow(pdf: FPDF, width: float, height: float, text: str, x: float | None = None
          ) -> None:
    """Write a wrapped paragraph and leave the cursor on the next line.

    multi_cell otherwise parks the cursor at the right edge of the cell it just
    filled, so the following block starts mid-page and runs off the margin.
    """
    pdf.set_x(PAGE_MARGIN if x is None else x)
    pdf.multi_cell(
        width, height, _latin1(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )


class _Doc(FPDF):
    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", size=7.5)
        self.set_text_color(*MUTED)
        self.cell(
            0, 4,
            _latin1(f"Institute for Protein Innovation    Page {self.page_no()}"),
            align="C",
        )


def render_checklist(
    concepts: dict[str, Concept],
    concept_ids: list[str],
    generated_on: str = "",
) -> ChecklistDocument | None:
    """Lay the cited concepts' checklists into the standard document.

    Returns None when nothing cited carries a checklist, which is the caller's
    signal not to offer a download rather than to serve an empty one.
    """
    selected = checklist_concepts(concepts, concept_ids)
    if not selected:
        return None

    pdf = _Doc(format="letter", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
    pdf.add_page()
    width = pdf.w - 2 * PAGE_MARGIN

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*DISPLAY)
    _flow(pdf, width, 7, "Antibody validation checklist")
    pdf.ln(1)

    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(*MUTED)
    _flow(pdf, width, 4.6, ", ".join(c.title for c in selected))
    if generated_on:
        _flow(pdf, width, 4.6, f"Prepared {generated_on}")
    pdf.ln(3)

    pdf.set_draw_color(*LINE)
    pdf.set_line_width(0.2)
    pdf.line(PAGE_MARGIN, pdf.get_y(), pdf.w - PAGE_MARGIN, pdf.get_y())
    pdf.ln(5)

    indent = PAGE_MARGIN + BOX + 3
    item_width = width - BOX - 3

    for concept in selected:
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(*DISPLAY)
        _flow(pdf, width, 5.5, concept.title)
        pdf.ln(1.5)

        for entry in concept.checklist:
            top = pdf.get_y()
            pdf.set_draw_color(*BODY)
            pdf.set_line_width(0.25)
            pdf.rect(PAGE_MARGIN, top + 1.1, BOX, BOX)

            pdf.set_xy(indent, top)
            pdf.set_font("Helvetica", size=9.5)
            pdf.set_text_color(*DISPLAY)
            _flow(pdf, item_width, 4.8, str(entry["item"]), x=indent)

            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(*MUTED)
            _flow(pdf, item_width, 4.2, f"Confirms: {entry['proves']}", x=indent)
            pdf.ln(2.2)
        pdf.ln(2)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MUTED)
    _flow(pdf, width, 4, SCOPE_NOTE)

    published = _published_sources(selected)
    if published:
        pdf.ln(3)
        # Keep the reference block whole. Splitting it leaves an orphan line or
        # two on a page of their own, which on a sheet meant for a bench is
        # just a second page to lose.
        needed = 5 + 4.4 * len(published)
        if pdf.get_y() + needed > pdf.h - pdf.b_margin:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*BODY)
        _flow(pdf, width, 4, "References")
        pdf.set_font("Helvetica", size=8)
        pdf.set_text_color(*MUTED)
        for label in published:
            _flow(pdf, width, 3.8, label)

    return ChecklistDocument(
        filename=CHECKLIST_FILENAME,
        body=bytes(pdf.output()),
    )


def _published_sources(selected: list[Concept]) -> list[str]:
    """Deduplicated citations for the concepts in the document.

    Filtered through the same is_publishable the widget's sources row uses, so
    a printed reference list can never carry something the screen withholds.
    The short byline form is used rather than the full Vancouver label, keeping
    a reference list that a reader can scan on paper.
    """
    seen: set[str] = set()
    out: list[str] = []
    for concept in selected:
        for source in concept.sources:
            if not is_publishable(source):
                continue
            short = str(source.get("short", "")).strip()
            if not short:
                label = str(source.get("label", "")).strip()
                if label and label not in seen:
                    seen.add(label)
                    out.append(label)
                continue
            if short in seen:
                continue
            seen.add(short)
            byline = ", ".join(
                p for p in (short, str(source.get("journal", "")).strip()) if p
            )
            title = str(source.get("title", "")).strip()
            out.append(f"{byline}. {title}." if title else f"{byline}.")
    return out
