"""Typed shapes for the published-datasheet ingest.

The enums and `Provenance` come from `packages.antibody` rather than being
redeclared here, because those are what the tool surface already returns and a
second vocabulary for the same concepts is how `western_blot` and `WB` end up
meaning different things in one system. What is new here is the datasheet's own
structure: an Overview block, a tested-applications table, and the version
stamp that identifies which revision of the document a field was read from.

`DatasheetRecord` is deliberately not `AntibodyRecord`. `AntibodyRecord` is the
tool-facing projection and carries a standing placeholder notice; this is the
ingest-facing record and carries everything the datasheet says, including the
verbatim strings a later normalization step will need to argue with. Choosing
which subset crosses into the tool surface is the next piece of work and wants
its own review, so no converter is offered yet.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from packages.antibody import Application, Provenance, Species


class AssayResult(StrEnum):
    """Verdict a datasheet records against one tested application.

    A closed set on purpose. The catalog uses exactly two words today, and a
    third appearing is a change in how IPI reports results, which is worth an
    ingest failure rather than a silent pass-through.
    """

    POSITIVE = "positive"
    NEGATIVE = "negative"


class ProductIndexEntry(BaseModel):
    """One published product as the site's REST index reports it.

    Carries `modified` because change detection is the reason to read the index
    at all: re-fetching ninety-odd PDFs to find the two that moved is the kind
    of job that gets switched off.
    """

    product_id: int = Field(description="WordPress post id, stable across renames.")
    slug: str = Field(description="URL slug, the natural key for a product page.")
    title: str = Field(description="Product name with its clone, entities decoded.")
    permalink: str = Field(description="Public product page URL.")
    modified: str = Field(description="Site-local last-modified timestamp, ISO 8601.")


class ReactivityClaim(BaseModel):
    """One species the datasheet reports reactivity against, with its hedge.

    The qualifier is kept rather than dropped because `mouse (predicted)` and
    `mouse` are different claims, and an assistant that flattens them is
    asserting a test that was never run.
    """

    species: Species = Field(description="Species the claim is about.")
    qualifier: str | None = Field(
        default=None,
        description="Hedge the datasheet attached to this species, verbatim.",
    )


class TestedApplication(BaseModel):
    """One row of the IPI Tested Applications table.

    `label` is the datasheet's own wording and `application` is the canonical
    enum it maps onto. Both are kept: the enum is what a filter can use, and the
    label is what distinguishes `IF - Binding` from `IF - Specificity`, which
    are separate experiments the enum cannot tell apart.
    """

    label: str = Field(description="Application cell exactly as printed.")
    application: Application = Field(
        description="Canonical application the row maps onto."
    )
    tested_concentration: str = Field(description="Concentration cell, verbatim.")
    result: AssayResult = Field(description="Reported verdict for this row.")
    reference: str = Field(description="Reference cell, verbatim.")
    reference_doi: str | None = Field(
        default=None,
        description="Resolvable DOI URL, absent when the row cites no publication.",
    )


class DatasheetRecord(BaseModel):
    """One published datasheet, parsed whole or not at all.

    Every field here was asserted during parsing. There is no partial record:
    an antibody Abbie has no record for makes her abstain, which is a correct
    answer, while an antibody with half a record makes her confident about the
    half she has.
    """

    slug: str = Field(description="Product slug this datasheet was reached through.")
    antigen: str = Field(description="Antigen line, verbatim, aliases included.")
    immunogen: str = Field(description="Immunogen description, verbatim.")
    host_species: Species = Field(description="Species the reagent was raised in.")
    isotype: str = Field(description="Isotype as printed, for example IgG1.")
    clonality: str = Field(description="Clonality line, verbatim.")
    clone_name: str = Field(description="Clone name, the catalog's lookup key.")
    rrid: str = Field(description="Research Resource Identifier, AB_ prefixed.")
    ipi_id: str = Field(description="IPI internal identifier printed on every page.")
    specificity: str = Field(description="Specificity statement, verbatim.")
    species_reactivity: str = Field(description="Reactivity line as printed.")
    reactivity: list[ReactivityClaim] = Field(
        description="Reactivity line resolved to species, empty for a control."
    )
    amount: str | None = Field(
        default=None,
        description="Vial amount, absent from the newer datasheet template.",
    )
    concentration: str = Field(description="Supplied concentration, verbatim.")
    purification: str = Field(description="Expression line and purification method.")
    storage_buffer: str = Field(description="Storage buffer composition.")
    shipping: str = Field(description="Shipping conditions.")
    storage: str = Field(description="Storage conditions.")
    datasheet_version: str = Field(description="Version stamp, for example 2026.05.22.")
    tested_applications: list[TestedApplication] = Field(
        description="IPI Tested Applications rows, external lab data excluded."
    )
    footnotes: list[str] = Field(
        description="Footnotes under the table, which is where limits are stated."
    )
    provenance: Provenance = Field(description="Row-level source and build stamp.")


class SkippedProduct(BaseModel):
    """A published product that has no datasheet to parse.

    Reported rather than filtered out. A product missing from the extract with
    no explanation is indistinguishable from a product IPI does not sell, and
    the difference matters to whoever is deciding what to publish next.
    """

    slug: str = Field(description="Product slug.")
    title: str = Field(description="Product name from the index.")
    permalink: str = Field(description="Public product page URL.")
    reason: str = Field(description="Why no datasheet was available.")


class IngestFailure(BaseModel):
    """A product whose datasheet was found but could not be turned into a record."""

    slug: str = Field(description="Product slug.")
    title: str = Field(description="Product name from the index.")
    source_url: str = Field(description="URL the failure was reached through.")
    stage: str = Field(description="Which step failed: fetch, extract, or parse.")
    reason: str = Field(description="Exact reason, quoting the offending value.")


class IngestResult(BaseModel):
    """Everything one ingest run produced, successes and failures together.

    Failures are part of the result rather than a log line, because the summary
    is the artifact a reviewer reads to decide whether the catalog moved or the
    parser broke.
    """

    built_at: str = Field(description="Run timestamp, ISO 8601.")
    products_indexed: int = Field(description="Published products the index returned.")
    records: list[DatasheetRecord] = Field(description="Datasheets parsed in full.")
    skipped: list[SkippedProduct] = Field(description="Products with no datasheet.")
    failures: list[IngestFailure] = Field(description="Datasheets that did not parse.")
