"""Placeholder catalog tools, standing in until the published datasheet lands.

Nothing here reads a database, a file, or a network. Every record below is
fixed, invented, and labeled as such, and the identifiers and targets are
deliberately unlike anything IPI ships so a placeholder answer can never be
mistaken for a catalog answer. The module exists so the bounded tool loop is
testable before Stage 2's approved extract exists, and it is meant to be
replaced wholesale by the real connectors rather than grown into them.

The shape is not placeholder, though, and follows the tool-library rules that
are expensive to retrofit:

- transport-free. This package may import Pydantic and the standard library and
  may not import fastapi, fastmcp, starlette, openai, or slack_bolt, so the
  widget calls it in process and the MCP server and the Slack app become thin
  adapters over the same functions. test_antibody.py enforces that rather than
  leaving it to convention
- return types are Pydantic models with described fields, so a tool schema
  derives from them instead of being hand-written and then kept in sync
- parameters are enums, not free strings, because free text means the model
  sends western, westernblot, and Western Blot and a real query misses all
  three. Application deliberately includes values with no data behind them, so
  asking about IHC returns unassessed rather than a validation error
- every row carries provenance, which on a tool surface is the only control
  left, because nothing of ours composes the answer
- there is no scope or include_unpublished parameter. Scope belongs to the
  connection handle at construction, because a parameter lands in the tool
  schema and becomes settable by the model. There is no handle yet because
  there is no data source yet
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# Repeated into every record and every search result on purpose. The model sees
# this text, so a reply composed over these rows has been told in band that the
# rows are invented, and a demo that slips past the feature flag says so out
# loud rather than inventing a plausible catalog.
PLACEHOLDER_NOTICE = (
    "Placeholder data. These records are invented for pipeline testing and"
    " describe no real reagent. The published datasheet ingest replaces them."
)

# RFC 2606 reserves .invalid, so provenance links here can never resolve to
# something a reader would follow.
PLACEHOLDER_SOURCE = "https://placeholder.invalid/awaiting-datasheet-ingest"

DEFAULT_SEARCH_LIMIT = 5
MAX_SEARCH_LIMIT = 25


class Application(StrEnum):
    """Assay a reagent may be assessed in.

    Values with no assessment behind them are members anyway. A schema that
    rejects IHC cannot express the interpretive principle that absence of data
    is not evidence of failure, because the question never reaches the tool.
    """

    WESTERN_BLOT = "western_blot"
    IMMUNOFLUORESCENCE = "immunofluorescence"
    IMMUNOHISTOCHEMISTRY = "immunohistochemistry"
    FLOW_CYTOMETRY = "flow_cytometry"
    ELISA = "elisa"
    IMMUNOPRECIPITATION = "immunoprecipitation"


class Species(StrEnum):
    """Reactivity species, canonical rather than as a visitor phrases it."""

    HUMAN = "human"
    MOUSE = "mouse"
    RAT = "rat"


class Provenance(BaseModel):
    """Where one row came from and which build produced it.

    Carried per row rather than per response because a synthesized reply mixes
    rows from several fetches, and a reader asking where one claim came from is
    asking about that row.
    """

    source_url: str = Field(description="Public page this row was derived from.")
    manifest_version: str = Field(
        description="Publication manifest that approved the row for release."
    )
    built_at: str = Field(description="Build timestamp of the extract, ISO 8601.")


class AntibodyRecord(BaseModel):
    """One catalog entry as the tool surface reports it."""

    identifier: str = Field(description="Catalog identifier, the lookup key.")
    target: str = Field(description="Canonical target symbol.")
    clone: str = Field(description="Clone name.")
    host_species: Species = Field(description="Species the reagent was raised in.")
    reactivity: list[Species] = Field(
        description="Species the reagent is reported to react with."
    )
    assessed_applications: list[Application] = Field(
        description=(
            "Applications with assessment data behind them. An application"
            " absent from this list is unassessed, which is not a failure."
        )
    )
    provenance: Provenance = Field(description="Row-level source and build stamp.")
    notice: str = Field(
        default=PLACEHOLDER_NOTICE,
        description="Standing warning that this row is invented test data.",
    )


class AntibodyLookup(BaseModel):
    """Result of one identifier lookup, including the miss.

    A miss is a structured answer rather than a null, because the model reads
    this payload and "no such identifier" and "the lookup failed" have to be
    distinguishable from each other in it.
    """

    found: bool = Field(description="Whether an entry matched the identifier.")
    record: AntibodyRecord | None = Field(
        default=None, description="The matching entry, absent on a miss."
    )
    note: str = Field(
        default=PLACEHOLDER_NOTICE, description="Standing warning about the data."
    )


class AntibodySearch(BaseModel):
    """Result of one catalog search."""

    hits: list[AntibodyRecord] = Field(description="Entries matching every filter.")
    truncated: bool = Field(
        description="Whether matches were dropped to satisfy the limit."
    )
    note: str = Field(
        default=PLACEHOLDER_NOTICE, description="Standing warning about the data."
    )


class GetAntibodyArgs(BaseModel):
    """Arguments to get_antibody, and the source of its published schema."""

    identifier: str = Field(
        description="Catalog identifier of the entry to fetch, exact match."
    )


class SearchAntibodiesArgs(BaseModel):
    """Arguments to search_antibodies, and the source of its published schema.

    Every filter is optional, and omitting all of them lists the catalog. That
    is deliberate: a model that cannot ask what exists guesses at target names
    instead.
    """

    target: str | None = Field(
        default=None, description="Target symbol to match, case-insensitive."
    )
    application: Application | None = Field(
        default=None, description="Restrict to entries assessed in this application."
    )
    species: Species | None = Field(
        default=None, description="Restrict to entries reactive with this species."
    )
    limit: int = Field(
        default=DEFAULT_SEARCH_LIMIT,
        description=f"Maximum entries to return, at most {MAX_SEARCH_LIMIT}.",
    )


def _placeholder_provenance() -> Provenance:
    return Provenance(
        source_url=PLACEHOLDER_SOURCE,
        manifest_version="placeholder-0",
        built_at="1970-01-01T00:00:00Z",
    )


# Fixed, invented, and enumerable. Three rows are enough to exercise a hit, a
# miss, and a filter that excludes, which is everything the loop tests need.
PLACEHOLDER_RECORDS: tuple[AntibodyRecord, ...] = (
    AntibodyRecord(
        identifier="PLACEHOLDER-0001",
        target="EXAMPLEGENE1",
        clone="FAKE-1A1",
        host_species=Species.RAT,
        reactivity=[Species.HUMAN, Species.MOUSE],
        assessed_applications=[
            Application.WESTERN_BLOT,
            Application.IMMUNOFLUORESCENCE,
        ],
        provenance=_placeholder_provenance(),
    ),
    AntibodyRecord(
        identifier="PLACEHOLDER-0002",
        target="EXAMPLEGENE1",
        clone="FAKE-2B4",
        host_species=Species.MOUSE,
        reactivity=[Species.HUMAN],
        assessed_applications=[Application.ELISA],
        provenance=_placeholder_provenance(),
    ),
    AntibodyRecord(
        identifier="PLACEHOLDER-0003",
        target="EXAMPLEGENE2",
        clone="FAKE-3C9",
        host_species=Species.RAT,
        reactivity=[Species.MOUSE, Species.RAT],
        assessed_applications=[Application.WESTERN_BLOT],
        provenance=_placeholder_provenance(),
    ),
)


def get_antibody(identifier: str) -> AntibodyLookup:
    """Fetch one placeholder entry by catalog identifier.

    Matching ignores case and surrounding whitespace, because an identifier
    reaches this function by way of a model copying it out of a visitor's
    question and neither of those variations is a different reagent.
    """
    wanted = identifier.strip().casefold()
    for record in PLACEHOLDER_RECORDS:
        if record.identifier.casefold() == wanted:
            return AntibodyLookup(found=True, record=record)
    return AntibodyLookup(found=False)


def search_antibodies(
    target: str | None = None,
    application: Application | None = None,
    species: Species | None = None,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> AntibodySearch:
    """Search placeholder entries by target, application, and reactivity.

    Filters combine as an intersection, and an omitted filter constrains
    nothing. The limit is clamped rather than rejected: a model asking for two
    hundred rows has made a context-window mistake, not a request worth failing
    a turn over.
    """
    bounded = max(1, min(limit, MAX_SEARCH_LIMIT))
    wanted_target = target.strip().casefold() if target else None
    matches = [
        record
        for record in PLACEHOLDER_RECORDS
        if (wanted_target is None or record.target.casefold() == wanted_target)
        and (application is None or application in record.assessed_applications)
        and (species is None or species in record.reactivity)
    ]
    return AntibodySearch(
        hits=matches[:bounded], truncated=len(matches) > bounded
    )
