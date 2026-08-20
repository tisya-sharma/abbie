"""Unit tests for one whole ingest run. No key and no network:

    python3 -m unittest packages.catalog.test_ingest

The run is driven through its reader, fetcher and extractor seams, so what is
under test is the accounting: that every indexed product ends up in exactly one
of parsed, skipped or failed, and that none of them is dropped.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path

from packages.catalog.datasheet import DatasheetFetchError, FetchedDatasheet
from packages.catalog.index import IndexPage, entries_from_payload
from packages.catalog.ingest import ingest_catalog

FIXTURES = Path(__file__).resolve().parent / "fixtures"

WITH_DATASHEET = "anti-cntn2-tag-1-ipi-cntn2-57"

WITHOUT_DATASHEET = "anti-integrin-alpha-l-ipi-ts2-4"

UNPARSEABLE = "anti-neurexin-1-beta-ipi-nrxn1b-35"

PAGES_BY_SLUG = {
    WITH_DATASHEET: FIXTURES.joinpath("cntn2-57.txt").read_text().split("\f"),
    UNPARSEABLE: FIXTURES.joinpath("nrxn1b-35.txt").read_text().split("\f"),
}

TITLES = {
    WITH_DATASHEET: "Anti-CNTN2 (TAG-1) [IPI-CNTN2.57]",
    WITHOUT_DATASHEET: "Anti-Integrin alpha L [IPI-TS2/4]",
    UNPARSEABLE: "Anti-Neurexin-1-beta [IPI-NRXN1b.35]",
}


def product(slug: str, product_id: int) -> dict:
    return {
        "id": product_id,
        "slug": slug,
        "title": {"rendered": TITLES[slug]},
        "link": f"https://proteininnovation.org/product/{slug}/",
        "status": "publish",
        "modified": "2026-08-17T13:26:06",
    }


def read_one_page(slugs: list[str]):
    payload = [product(slug, index) for index, slug in enumerate(slugs, start=1)]

    def read_page(page: int, per_page: int) -> IndexPage:
        return IndexPage(
            entries=entries_from_payload(payload),
            total_products=len(payload),
            total_pages=1,
        )

    return read_page


def fetch_from_fixtures(permalink: str) -> FetchedDatasheet:
    slug = permalink.rstrip("/").rsplit("/", 1)[-1]
    if slug not in PAGES_BY_SLUG:
        return FetchedDatasheet(
            None, None, "product permalink serves the storefront page"
        )
    return FetchedDatasheet(
        f"https://proteininnovation.org/{slug}.pdf", slug.encode(), None
    )


def extract_from_fixtures(content: bytes) -> list[str]:
    return PAGES_BY_SLUG[content.decode()]


def run(slugs: list[str], **overrides):
    return ingest_catalog(
        read_page=read_one_page(slugs),
        fetch=overrides.get("fetch", fetch_from_fixtures),
        extract=overrides.get("extract", extract_from_fixtures),
        clock=lambda: datetime(2026, 8, 19, tzinfo=UTC),
    )


class AccountingTests(unittest.TestCase):
    def test_every_indexed_product_lands_in_exactly_one_list(self):
        result = run([WITH_DATASHEET, WITHOUT_DATASHEET, UNPARSEABLE])
        self.assertEqual(result.products_indexed, 3)
        self.assertEqual(
            len(result.records) + len(result.skipped) + len(result.failures),
            result.products_indexed,
        )

    def test_a_product_with_no_datasheet_is_reported_rather_than_skipped_silently(self):
        result = run([WITH_DATASHEET, WITHOUT_DATASHEET])
        self.assertEqual([entry.slug for entry in result.skipped], [WITHOUT_DATASHEET])
        self.assertIn("storefront", result.skipped[0].reason)
        self.assertEqual(result.skipped[0].title, TITLES[WITHOUT_DATASHEET])

    def test_a_datasheet_that_does_not_parse_produces_a_failure_and_no_record(self):
        result = run([UNPARSEABLE])
        self.assertEqual(result.records, [])
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0].stage, "parse")
        self.assertIn("Amount", result.failures[0].reason)

    def test_a_fetch_that_fails_does_not_abandon_the_rest_of_the_run(self):
        def fetch(permalink: str) -> FetchedDatasheet:
            if UNPARSEABLE in permalink:
                raise DatasheetFetchError(
                    f"{permalink} could not be fetched: timed out"
                )
            return fetch_from_fixtures(permalink)

        result = run([UNPARSEABLE, WITH_DATASHEET], fetch=fetch)
        self.assertEqual([record.slug for record in result.records], [WITH_DATASHEET])
        self.assertEqual(result.failures[0].stage, "fetch")
        self.assertIn("timed out", result.failures[0].reason)

    def test_the_run_timestamp_reaches_every_record(self):
        result = run([WITH_DATASHEET])
        self.assertEqual(result.built_at, "2026-08-19T00:00:00+00:00")
        self.assertEqual(result.records[0].provenance.built_at, result.built_at)


class TitleCrossCheckTests(unittest.TestCase):
    def test_a_product_page_pointing_at_another_clones_datasheet_is_refused(self):
        """The index and the PDF are separately maintained, and this is the one
        catalog error that would have Abbie answer about a different antibody."""
        payload_slug = WITH_DATASHEET

        def read_page(page: int, per_page: int) -> IndexPage:
            raw = product(payload_slug, 1)
            raw["title"]["rendered"] = "Anti-CNTN2 (TAG-1) [IPI-CNTN2.99]"
            return IndexPage(
                entries=entries_from_payload([raw]), total_products=1, total_pages=1
            )

        result = ingest_catalog(
            read_page=read_page,
            fetch=fetch_from_fixtures,
            extract=extract_from_fixtures,
            clock=lambda: datetime(2026, 8, 19, tzinfo=UTC),
        )
        self.assertEqual(result.records, [])
        self.assertIn("IPI-CNTN2.99", result.failures[0].reason)


if __name__ == "__main__":
    unittest.main()
