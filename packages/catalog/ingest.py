"""One ingest run: index, fetch, extract, parse, and account for every product.

Accounting is the point. A run over 94 published products that returns 57
records has said nothing useful unless it also says what happened to the other
37, so every product leaves this function in exactly one of three lists:
parsed, skipped for want of a datasheet, or failed with a reason. Silence about
a product is not an available outcome.

Why this is its own package: architecture.md's layout gives `packages/retrieval`
to corpus chunking and embeddings and `packages/antibody` to the transport-free
tool library, and neither can hold this. The tool library is forbidden a
transport and this needs one, and corpus retrieval is a different pipeline over
different material. So `packages/catalog` is new, and it is the only package
allowed to make outbound requests.

Where the database goes: nowhere yet. The roadmap puts Abbie's Postgres on
Cloud SQL at Stage 2 and this returns a value rather than writing rows, so the
seam is `IngestResult` itself. Persistence is one function that takes it and a
connection, and nothing above this line has to change to gain one.

The fetch, extract and clock are parameters so a test can drive a whole run
without a network. That is the only reason they are parameters.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime

from packages.catalog.datasheet import (
    DatasheetExtractError,
    DatasheetFetchError,
    FetchedDatasheet,
    extract_pages,
    fetch_datasheet,
)
from packages.catalog.index import PageReader, fetch_index, read_page_over_http
from packages.catalog.models import (
    DatasheetRecord,
    IngestFailure,
    IngestResult,
    ProductIndexEntry,
    SkippedProduct,
)
from packages.catalog.parse import DatasheetParseError, parse_datasheet

TITLE_CLONE = re.compile(r"\[([^\[\]]+)\]")

DatasheetFetcher = Callable[[str], FetchedDatasheet]
PageExtractor = Callable[[bytes], list[str]]
Clock = Callable[[], datetime]


def ingest_catalog(
    *,
    read_page: PageReader = read_page_over_http,
    fetch: DatasheetFetcher = fetch_datasheet,
    extract: PageExtractor = extract_pages,
    clock: Clock = lambda: datetime.now(UTC),
) -> IngestResult:
    """Run the whole ingest and return what it produced, failures included."""
    built_at = clock().isoformat(timespec="seconds")
    products = fetch_index(read_page=read_page)

    records: list[DatasheetRecord] = []
    skipped: list[SkippedProduct] = []
    failures: list[IngestFailure] = []

    for product in products:
        outcome = _ingest_product(
            product, fetch=fetch, extract=extract, built_at=built_at
        )
        if isinstance(outcome, DatasheetRecord):
            records.append(outcome)
        elif isinstance(outcome, SkippedProduct):
            skipped.append(outcome)
        else:
            failures.append(outcome)

    return IngestResult(
        built_at=built_at,
        products_indexed=len(products),
        records=records,
        skipped=skipped,
        failures=failures,
    )


def _ingest_product(
    product: ProductIndexEntry,
    *,
    fetch: DatasheetFetcher,
    extract: PageExtractor,
    built_at: str,
) -> DatasheetRecord | SkippedProduct | IngestFailure:
    try:
        fetched = fetch(product.permalink)
    except DatasheetFetchError as error:
        return _failure(product, product.permalink, "fetch", str(error))

    if fetched.content is None or fetched.pdf_url is None:
        return SkippedProduct(
            slug=product.slug,
            title=product.title,
            permalink=product.permalink,
            reason=fetched.reason or "no datasheet and no reason given",
        )

    try:
        pages = extract(fetched.content)
    except DatasheetExtractError as error:
        return _failure(product, fetched.pdf_url, "extract", str(error))

    try:
        record = parse_datasheet(
            pages,
            slug=product.slug,
            source_url=fetched.pdf_url,
            built_at=built_at,
        )
        _confirm_title_clone(product.title, record.clone_name)
    except DatasheetParseError as error:
        return _failure(product, fetched.pdf_url, "parse", str(error))

    return record


def _confirm_title_clone(title: str, clone_name: str) -> None:
    """The clone the storefront advertises has to be the clone on the datasheet.

    The index and the PDF are separately maintained, and a product page pointing
    at the wrong datasheet is the one catalog error that would make Abbie answer
    about a different antibody than the one she was asked about.
    """
    found = TITLE_CLONE.search(title)
    if not found:
        raise DatasheetParseError(
            f"product title {title!r} carries no bracketed clone name"
        )
    if found.group(1).strip() != clone_name:
        raise DatasheetParseError(
            f"product title names clone {found.group(1).strip()!r}"
            f" but its datasheet names {clone_name!r}"
        )


def _failure(
    product: ProductIndexEntry, source_url: str, stage: str, reason: str
) -> IngestFailure:
    return IngestFailure(
        slug=product.slug,
        title=product.title,
        source_url=source_url,
        stage=stage,
        reason=reason,
    )
