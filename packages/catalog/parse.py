"""Strict parser turning datasheet page text into one record, or into nothing.

The governing property, and the reason this file is written the way it is: a
datasheet either parses completely or produces no record and a stated reason.
There is no partial record and no defaulted field. An antibody Abbie has no
record for makes her abstain, and abstaining on a real product is a cost the
project has already accepted. An antibody with a half-parsed record makes her
answer confidently about the half that survived, which is the failure this
whole system exists to prevent.

So every field is asserted, every vocabulary is closed, and every assertion
raises `DatasheetParseError` naming the value that failed. Two consequences are
deliberate and should not be softened later:

- a new application name, result word, or reference style fails the ingest for
  that datasheet instead of being passed through unrecognized. The catalog
  changing its vocabulary is something a reviewer should be told about
- the applications table is cut at the Community Data heading. Those rows are
  external partner labs' observations, and folding them into IPI Tested
  Applications would attribute someone else's experiment to IPI

PDF text extraction is not tidy. Page 1 arrives as one long run in the older
template and as one label per line in the newer one, so parsing is anchored on
the label vocabulary after whitespace is collapsed, not on line structure. The
extractor also breaks the occasional heading across a line boundary, which is
why heading patterns tolerate whitespace between letters.
"""

from __future__ import annotations

import re

from packages.antibody import Application, Provenance, Species
from packages.catalog.models import (
    AssayResult,
    DatasheetRecord,
    ReactivityClaim,
    TestedApplication,
)


class DatasheetParseError(ValueError):
    """A datasheet did not parse cleanly, so it yields no record."""


# Label variants observed across the published catalog. Two templates are in
# circulation: the older one prints "Species reactivity", "Amount" and
# "Storage buffer", the newer one prints "Species" and "Storage Buffer" and
# drops the amount entirely. Both are accepted, anything else is not.
LABEL_VARIANTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("antigen", ("Antigen",)),
    ("immunogen", ("Immunogen",)),
    ("host_isotype", ("Host/isotype",)),
    ("clonality", ("Clonality",)),
    ("clone_name", ("Clone name",)),
    ("rrid", ("RRID",)),
    ("ipi_id", ("IPI ID",)),
    ("specificity", ("Specificity",)),
    ("species_reactivity", ("Species reactivity", "Species")),
    ("amount", ("Amount",)),
    ("concentration", ("Concentration",)),
    ("purification", ("Purification",)),
    ("storage_buffer", ("Storage buffer", "Storage Buffer")),
    ("shipping", ("Shipping",)),
    ("storage", ("Storage",)),
)

# Amount is absent from the newer template, so it is the one field whose
# absence is not a defect. Every other label appears on all 57 published
# datasheets, so its absence means the parse went wrong rather than that the
# datasheet was terse.
OPTIONAL_FIELDS = frozenset({"amount"})

FIELD_BY_LABEL = {
    label: field for field, labels in LABEL_VARIANTS for label in labels
}

# Longest first so "Storage buffer" wins over "Storage" at the same position,
# and "Species reactivity" over "Species".
_LABEL_ALTERNATION = "|".join(
    re.escape(label) for label in sorted(FIELD_BY_LABEL, key=len, reverse=True)
)

# The nav strip above the Overview block reads "Antibody Details | Antigen
# Details | References", so a bare Antigen anchor would take the navigation for
# the antigen field and swallow the rest of the block.
LABEL_ANCHOR = re.compile(rf"(?<![A-Za-z])({_LABEL_ALTERNATION})(?!\s+Details\b)\b")

# A backstop against one field absorbing its neighbours. Eight datasheets
# extract as a label column followed by a value column, and what catches those
# is the emptiness check below rather than this one. The bound is set well
# clear of the longest legitimate value in the published catalog, a 161
# character immunogen note, so nothing published today trips it.
MAX_FIELD_CHARS = 500

APPLICATIONS_HEADING = "IPI Tested Applications"

FOOTNOTE_MARKER = "‡"

PAGE_FURNITURE = ("FOR RESEARCH USE", "Institute for Protein Innovation")

VERSION_STAMP = re.compile(r"(?<![A-Za-z])v\s?(\d{4}\.\d{2}\.\d{2})\b")

HEADER_CLONE = re.compile(r"\[([^\[\]]+)\]")

RRID_VALUE = re.compile(r"AB_\d{4,}")

IPI_ID_VALUE = re.compile(r"TAB\d{7}(?:-\d{3})+")

CLONE_VALUE = re.compile(r"IPI-[A-Za-z0-9./_-]+")

HOST_ISOTYPE_VALUE = re.compile(r"([A-Za-z]+)\s*/\s*(Ig[A-Z]\d*)")

SPECIES_BY_NAME = {species.value: species for species in Species}

# The reactivity line for the isotype control, which is reactive against
# nothing by design.
NO_REACTIVITY_VALUES = frozenset({"n/a", "na", "none"})

REACTIVITY_PART = re.compile(r"([A-Za-z]+)(?:\s*\(([^()]*)\))?")

REFERENCE_DOI = re.compile(r"https://doi\.org/\S+")

UNPUBLISHED_REFERENCE = "Unpublished"

# Application names as the catalog prints them, reduced to the token before any
# dash or parenthetical. Only what is actually published is mapped: a name that
# is not here fails the datasheet on purpose, because guessing what a new assay
# abbreviation means is exactly the wrong instinct on this surface.
APPLICATION_BY_NAME = {
    "flow": Application.FLOW_CYTOMETRY,
    "flow cytometry": Application.FLOW_CYTOMETRY,
    "if": Application.IMMUNOFLUORESCENCE,
    "ihc": Application.IMMUNOHISTOCHEMISTRY,
    "wb": Application.WESTERN_BLOT,
    "spr": Application.SURFACE_PLASMON_RESONANCE,
    "cell display": Application.CELL_DISPLAY,
}

DASHES = "-‐‑‒–—"

_RESULT_WORDS = "|".join(result.value.capitalize() for result in AssayResult)

# Row shape: application, a concentration that starts with a digit or a
# comparison, a result word, and a reference. Anchoring the concentration on a
# leading digit is what separates a two-word application name from its value
# when the whole table has been flattened onto one line.
TABLE_ROW = re.compile(
    rf"\s*(?P<label>\S.*?)\s+(?P<concentration>[\d<>~].*?)"
    rf"\s+(?P<result>{_RESULT_WORDS})\s+(?P<reference>\S+)"
)

TABLE_HEADER = re.compile(
    rf"\s*{FOOTNOTE_MARKER}?\s*Applications?\s+Tested\s+[Cc]oncentration"
    r"\s+Results?\s+References?"
)


def _split_tolerant(word: str) -> str:
    """Pattern matching one word even when extraction split it across a line.

    pypdf renders "Community" as "Co mmunity" on several of these files, and
    the Community Data heading is the boundary that keeps external lab results
    out of IPI's own table, so it is not a heading that may quietly fail to
    match.
    """
    return r"\s*".join(re.escape(character) for character in word)


COMMUNITY_HEADING = re.compile(_split_tolerant("Community") + r"\s+Data")


# Non-breaking and thin spaces survive extraction and are not folded by a
# plain whitespace collapse, so they are translated first.
UNICODE_SPACES = str.maketrans({"\u00a0": " ", "\u2009": " ", "\u202f": " "})


def normalize(text: str) -> str:
    """Collapse a page to one whitespace-separated run.

    The two templates disagree about where line breaks fall and agree about
    label wording, so removing line structure removes the difference between
    them rather than losing information.
    """
    return re.sub(r"\s+", " ", text.translate(UNICODE_SPACES)).strip()


def parse_datasheet(
    pages: list[str],
    *,
    slug: str,
    source_url: str,
    built_at: str,
) -> DatasheetRecord:
    """Parse extracted datasheet pages into one record, or raise.

    `pages` is per-page text in document order. Later pages are read only to
    confirm they carry the same IPI identifier as page 1, which is the cheapest
    check available that a fetch returned one whole datasheet rather than two
    halves of different ones.
    """
    if not pages:
        raise DatasheetParseError("no pages to parse")

    front = normalize(pages[0])
    version = _parse_version(front)
    overview_end = front.find(APPLICATIONS_HEADING)
    if overview_end < 0:
        raise DatasheetParseError(f"page 1 carries no {APPLICATIONS_HEADING!r} heading")

    fields = _slice_overview(front[:overview_end])
    ipi_id = _match_exactly(IPI_ID_VALUE, fields["ipi_id"], "IPI ID")
    clone_name = _match_exactly(CLONE_VALUE, fields["clone_name"], "clone name")
    _confirm_header_clone(front, clone_name)
    _confirm_identifier_on_every_page(pages, ipi_id)

    host, isotype = _parse_host_isotype(fields["host_isotype"])
    applications, footnotes = _parse_applications(front[overview_end:])

    return DatasheetRecord(
        slug=slug,
        antigen=fields["antigen"],
        immunogen=fields["immunogen"],
        host_species=host,
        isotype=isotype,
        clonality=fields["clonality"],
        clone_name=clone_name,
        rrid=_match_exactly(RRID_VALUE, fields["rrid"], "RRID"),
        ipi_id=ipi_id,
        specificity=fields["specificity"],
        species_reactivity=fields["species_reactivity"],
        reactivity=_parse_reactivity(fields["species_reactivity"]),
        amount=fields.get("amount"),
        concentration=fields["concentration"],
        purification=fields["purification"],
        storage_buffer=fields["storage_buffer"],
        shipping=fields["shipping"],
        storage=fields["storage"],
        datasheet_version=version,
        tested_applications=applications,
        footnotes=footnotes,
        provenance=Provenance(
            source_url=source_url,
            # No publication manifest exists yet. Under the rule that a
            # published datasheet is the release decision, the revision stamp
            # on the document is what approved these values for the public, so
            # it stands in until the manifest at Stage 2 supersedes it.
            manifest_version=f"datasheet {version}",
            built_at=built_at,
        ),
    )


def _parse_version(front: str) -> str:
    """Read the revision stamp from the page header.

    Both templates print it, one as `v2026.05.22` and the other as
    `v 2026.08.14`, and it is the closest thing the public surface has to a
    content version, so a datasheet without one is not ingestible.
    """
    found = VERSION_STAMP.search(front)
    if not found:
        raise DatasheetParseError("page 1 carries no version stamp")
    return found.group(1)


def _slice_overview(overview: str) -> dict[str, str]:
    """Split the Overview block into label and value by anchoring on labels.

    Each value is whatever lies between its own label and the next one. That is
    only safe because the label vocabulary is closed and checked afterwards for
    emptiness, which is what catches the datasheets whose two columns extract as
    two separate runs of text.
    """
    anchors = list(LABEL_ANCHOR.finditer(overview))
    fields: dict[str, str] = {}
    for position, anchor in enumerate(anchors):
        field = FIELD_BY_LABEL[anchor.group(1)]
        if field in fields:
            raise DatasheetParseError(
                f"overview carries {anchor.group(1)!r} more than once"
            )
        is_last = position + 1 == len(anchors)
        stop = len(overview) if is_last else anchors[position + 1].start()
        fields[field] = overview[anchor.end() : stop].strip()

    for field, labels in LABEL_VARIANTS:
        if field not in fields:
            if field in OPTIONAL_FIELDS:
                continue
            raise DatasheetParseError(f"overview has no {' or '.join(labels)} label")
        if not fields[field]:
            raise DatasheetParseError(
                f"overview label {' or '.join(labels)} has an empty value"
            )
        if len(fields[field]) > MAX_FIELD_CHARS:
            raise DatasheetParseError(
                f"overview value for {' or '.join(labels)} runs"
                f" {len(fields[field])} characters,"
                f" over the {MAX_FIELD_CHARS} allowed, so the block did not"
                " split cleanly"
            )
    return fields


def _match_exactly(pattern: re.Pattern[str], value: str, what: str) -> str:
    if not pattern.fullmatch(value):
        raise DatasheetParseError(f"{what} {value!r} is not in the expected format")
    return value


def _confirm_header_clone(front: str, clone_name: str) -> None:
    """The clone in the page header has to be the clone in the Overview block.

    Two independent printings of the same fact, so disagreeing means the page
    was assembled from more than one source and no field on it can be trusted.
    """
    found = HEADER_CLONE.search(front)
    if not found:
        raise DatasheetParseError("page 1 header carries no bracketed clone name")
    if found.group(1).strip() != clone_name:
        raise DatasheetParseError(
            f"page header names clone {found.group(1).strip()!r}"
            f" but the overview names {clone_name!r}"
        )


def _confirm_identifier_on_every_page(pages: list[str], ipi_id: str) -> None:
    absent = [
        number
        for number, page in enumerate(pages, start=1)
        if ipi_id not in normalize(page)
    ]
    if absent:
        raise DatasheetParseError(
            f"IPI ID {ipi_id} is absent from page {', '.join(str(n) for n in absent)}"
            f" of {len(pages)}"
        )


def _parse_host_isotype(value: str) -> tuple[Species, str]:
    """Split `Rabbit/IgG` into a canonical host species and a printed isotype."""
    found = HOST_ISOTYPE_VALUE.fullmatch(value)
    if not found:
        raise DatasheetParseError(f"host/isotype {value!r} is not host/isotype shaped")
    host = SPECIES_BY_NAME.get(found.group(1).casefold())
    if host is None:
        raise DatasheetParseError(
            f"host species {found.group(1)!r} is not a known species"
        )
    return host, found.group(2)


def _parse_reactivity(value: str) -> list[ReactivityClaim]:
    """Resolve the reactivity line to species, refusing anything ambiguous.

    A parenthetical that names a second species is rejected rather than
    interpreted. `human (mouse not tested)` and `human (mouse)` would parse the
    same way under any rule simple enough to write here, and they mean opposite
    things about mouse.
    """
    if value.casefold() in NO_REACTIVITY_VALUES:
        return []

    claims: list[ReactivityClaim] = []
    for part in re.split(r"\s+and\s+", value):
        found = REACTIVITY_PART.fullmatch(part.strip())
        if not found:
            raise DatasheetParseError(
                f"reactivity term {part.strip()!r} is not a species term"
            )
        species = SPECIES_BY_NAME.get(found.group(1).casefold())
        if species is None:
            raise DatasheetParseError(
                f"reactivity names {found.group(1)!r}, not a known species"
            )
        qualifier = (found.group(2) or "").strip() or None
        if qualifier and _names_a_species(qualifier):
            raise DatasheetParseError(
                f"reactivity qualifier {qualifier!r} names another species,"
                " which this parser will not guess the meaning of"
            )
        if any(claim.species is species for claim in claims):
            raise DatasheetParseError(
                f"reactivity names {species.value} more than once"
            )
        claims.append(ReactivityClaim(species=species, qualifier=qualifier))

    if not claims:
        raise DatasheetParseError(f"reactivity line {value!r} resolved to no species")
    return claims


def _names_a_species(text: str) -> bool:
    lowered = text.casefold()
    return any(re.search(rf"\b{name}\b", lowered) for name in SPECIES_BY_NAME)


def _parse_applications(section: str) -> tuple[list[TestedApplication], list[str]]:
    """Parse the IPI Tested Applications table and the footnotes under it.

    The table is required to consume its own region completely. A row that does
    not match leaves text behind, and leftover text means the shape assumed
    here is wrong, which is worth failing over rather than reporting whichever
    rows happened to match.
    """
    community = COMMUNITY_HEADING.search(section)
    table = section[: community.start()] if community else section
    table = table[len(APPLICATIONS_HEADING) :]

    header = TABLE_HEADER.match(table)
    if not header:
        raise DatasheetParseError(
            "applications table has no recognizable column header"
        )

    body = table[header.end() :]
    marker = body.find(FOOTNOTE_MARKER)
    if marker >= 0:
        rows_text, footnote_text = body[:marker], body[marker:]
    else:
        rows_text, footnote_text = body, ""

    rows = _parse_rows(_trim_page_furniture(rows_text))
    if not rows:
        raise DatasheetParseError("applications table lists no rows")
    return rows, _parse_footnotes(footnote_text)


def _trim_page_furniture(text: str) -> str:
    cut = len(text)
    for furniture in PAGE_FURNITURE:
        found = text.find(furniture)
        if found >= 0:
            cut = min(cut, found)
    return text[:cut]


def _parse_rows(body: str) -> list[TestedApplication]:
    rows: list[TestedApplication] = []
    position = 0
    while position < len(body):
        if not body[position:].strip():
            break
        found = TABLE_ROW.match(body, position)
        if not found:
            raise DatasheetParseError(
                f"applications table has unparsed text after {len(rows)} rows:"
                f" {body[position:].strip()[:120]!r}"
            )
        label = found.group("label").strip()
        rows.append(
            TestedApplication(
                label=label,
                application=_application_for(label),
                tested_concentration=found.group("concentration").strip(),
                result=AssayResult(found.group("result").casefold()),
                reference=found.group("reference"),
                reference_doi=_reference_doi(found.group("reference")),
            )
        )
        position = found.end()
    return rows


def _application_for(label: str) -> Application:
    """Map a printed application name onto the canonical enum.

    The published names vary in ways that are not distinctions: `IF – Binding`,
    `IF - Binding` and `IF- Binding` all appear, and `IHC (cerebellum)` names a
    tissue rather than a different assay. What follows the dash is kept on the
    row's label because it names a different experiment, and only the head
    token decides the application.
    """
    head = re.split(rf"[{DASHES}]", label, maxsplit=1)[0]
    head = re.sub(r"\([^()]*\)", " ", head)
    name = re.sub(r"\s+", " ", head).strip().casefold()
    application = APPLICATION_BY_NAME.get(name)
    if application is None:
        raise DatasheetParseError(
            f"application {label!r} reduces to {name!r},"
            " which is not a known application"
        )
    return application


def _reference_doi(reference: str) -> str | None:
    if REFERENCE_DOI.fullmatch(reference):
        return reference
    if reference == UNPUBLISHED_REFERENCE:
        return None
    raise DatasheetParseError(
        f"reference {reference!r} is neither a doi.org URL"
        f" nor {UNPUBLISHED_REFERENCE!r}"
    )


def _parse_footnotes(text: str) -> list[str]:
    """Collect the footnotes under the table.

    Worth keeping rather than dropping: `Not suitable for WB application` is a
    negative result about an assay that has no row in the table, so an extract
    without the footnotes reads as though western blot was never considered.
    """
    footnotes: list[str] = []
    for piece in _trim_page_furniture(text).split(FOOTNOTE_MARKER):
        cleaned = piece.strip()
        if cleaned:
            footnotes.append(cleaned)
    return footnotes
