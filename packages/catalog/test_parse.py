"""Unit tests for the strict datasheet parser. No key and no network:

    python3 -m unittest packages.catalog.test_parse

Every input is text extracted from a real published datasheet and committed
under fixtures/. The failure cases are either datasheets that genuinely fail
today or a single edited field, so that what is being tested is the parser's
refusal and not a hand-built document nobody ships.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from packages.antibody import Application, Species
from packages.catalog.models import AssayResult
from packages.catalog.parse import DatasheetParseError, parse_datasheet

FIXTURES = Path(__file__).resolve().parent / "fixtures"

PAGE_SEPARATOR = "\f"


def load_pages(name: str) -> list[str]:
    return FIXTURES.joinpath(f"{name}.txt").read_text().split(PAGE_SEPARATOR)


def parse(name: str, pages: list[str] | None = None):
    return parse_datasheet(
        pages if pages is not None else load_pages(name),
        slug=name,
        source_url=f"https://proteininnovation.org/{name}.pdf",
        built_at="2026-08-19T00:00:00+00:00",
    )


class WellFormedDatasheetTests(unittest.TestCase):
    def test_the_identity_fields_come_out_whole(self):
        record = parse("cntn2-57")
        self.assertEqual(record.antigen, "CNTN2 (TAG-1)")
        self.assertEqual(record.clone_name, "IPI-CNTN2.57")
        self.assertEqual(record.rrid, "AB_3740901")
        self.assertEqual(record.ipi_id, "TAB0017429-013")
        self.assertEqual(record.host_species, Species.RABBIT)
        self.assertEqual(record.isotype, "IgG")
        self.assertEqual(record.clonality, "Recombinant monoclonal")
        self.assertEqual(
            record.specificity, "CNTN2; Does not cross-react with other CNTNs."
        )
        self.assertEqual(record.datasheet_version, "2026.05.22")

    def test_reactivity_resolves_to_species(self):
        record = parse("cntn2-57")
        self.assertEqual(
            [(claim.species, claim.qualifier) for claim in record.reactivity],
            [(Species.HUMAN, None), (Species.MOUSE, None)],
        )
        self.assertEqual(record.species_reactivity, "human and mouse")

    def test_the_applications_table_comes_out_row_by_row(self):
        record = parse("cntn2-57")
        self.assertEqual(
            [row.label for row in record.tested_applications],
            ["Flow", "IF – Binding", "IF – Specificity", "SPR", "IHC"],
        )
        self.assertEqual(
            [row.application for row in record.tested_applications],
            [
                Application.FLOW_CYTOMETRY,
                Application.IMMUNOFLUORESCENCE,
                Application.IMMUNOFLUORESCENCE,
                Application.SURFACE_PLASMON_RESONANCE,
                Application.IMMUNOHISTOCHEMISTRY,
            ],
        )
        first = record.tested_applications[0]
        self.assertEqual(first.tested_concentration, "0.66-100 μg/mL")
        self.assertEqual(first.result, AssayResult.POSITIVE)
        self.assertEqual(first.reference_doi, "https://doi.org/10.57733/addgene.5f7com")

    def test_provenance_carries_the_source_and_the_datasheet_revision(self):
        record = parse("cntn2-57")
        self.assertEqual(
            record.provenance.source_url,
            "https://proteininnovation.org/cntn2-57.pdf",
        )
        self.assertEqual(record.provenance.manifest_version, "datasheet 2026.05.22")
        self.assertEqual(record.provenance.built_at, "2026-08-19T00:00:00+00:00")


class TemplateVariantTests(unittest.TestCase):
    def test_the_newer_template_parses_under_its_own_labels(self):
        """Species rather than Species reactivity, and Storage Buffer capitalized."""
        record = parse("mntng1-4")
        self.assertEqual(record.species_reactivity, "human and mouse")
        self.assertEqual(record.storage_buffer, "PBS, pH 7.4")
        self.assertEqual(record.datasheet_version, "2026.08.14")

    def test_an_amount_absent_from_the_template_is_not_an_error(self):
        self.assertIsNone(parse("mntng1-4").amount)
        self.assertEqual(parse("cntn2-57").amount, "100 μg")


class NegativeResultTests(unittest.TestCase):
    def test_a_negative_row_is_reported_as_negative(self):
        rows = {row.label: row for row in parse("gpc1-21").tested_applications}
        self.assertEqual(rows["WB"].result, AssayResult.NEGATIVE)
        self.assertEqual(rows["WB"].application, Application.WESTERN_BLOT)

    def test_a_row_citing_no_publication_carries_no_doi(self):
        rows = {row.label: row for row in parse("gpc1-21").tested_applications}
        self.assertEqual(rows["WB"].reference, "Unpublished")
        self.assertIsNone(rows["WB"].reference_doi)

    def test_the_not_suitable_footnote_is_kept(self):
        self.assertEqual(
            parse("gpc1-21").footnotes, ["Not suitable for WB application."]
        )

    def test_external_lab_rows_are_not_reported_as_ipi_tested(self):
        """gpc1-21 carries a Community Data table listing an IHC result.

        That row is another lab's observation. Reading it into IPI Tested
        Applications would attribute an experiment IPI did not run.
        """
        labels = [row.label for row in parse("gpc1-21").tested_applications]
        self.assertEqual(labels, ["Cell Display", "Flow", "IF", "WB"])


class RefusalTests(unittest.TestCase):
    def test_a_datasheet_missing_a_required_value_yields_no_record(self):
        """nrxn1b-35 extracts as a label column then a value column.

        Half the Overview values come out empty. The parser has no way to pair
        them back up that is not a guess, so it produces nothing.
        """
        with self.assertRaises(DatasheetParseError) as raised:
            parse("nrxn1b-35")
        self.assertIn("Amount", str(raised.exception))

    def test_a_reactivity_qualifier_naming_another_species_is_refused(self):
        """ntn1-45 reads `human (mouse not tested)`, which is not `human (mouse)`."""
        with self.assertRaises(DatasheetParseError) as raised:
            parse("ntn1-45")
        self.assertIn("mouse not tested", str(raised.exception))

    def test_a_clone_disagreeing_with_its_own_header_is_refused(self):
        pages = load_pages("gpc1-21")
        pages[0] = pages[0].replace("Clone name IPI-GPC1.21", "Clone name IPI-GPC1.99")
        with self.assertRaises(DatasheetParseError) as raised:
            parse("gpc1-21", pages)
        self.assertIn("IPI-GPC1.99", str(raised.exception))

    def test_a_page_from_a_different_datasheet_is_refused(self):
        pages = load_pages("cntn2-57")[:2] + load_pages("mntng1-4")[1:2]
        with self.assertRaises(DatasheetParseError) as raised:
            parse("cntn2-57", pages)
        self.assertIn("TAB0017429-013", str(raised.exception))

    def test_an_unrecognized_application_name_is_refused(self):
        pages = load_pages("cntn2-57")
        pages[0] = pages[0].replace("Flow 0.66-100", "Cryo-EM 0.66-100")
        with self.assertRaises(DatasheetParseError) as raised:
            parse("cntn2-57", pages)
        self.assertIn("Cryo-EM", str(raised.exception))

    def test_a_reference_that_is_not_a_doi_is_refused(self):
        pages = load_pages("cntn2-57")
        pages[0] = pages[0].replace(
            "https://doi.org/10.57733/addgene.5f7com", "https://example.org/somewhere"
        )
        with self.assertRaises(DatasheetParseError) as raised:
            parse("cntn2-57", pages)
        self.assertIn("example.org", str(raised.exception))

    def test_a_malformed_rrid_is_refused(self):
        pages = load_pages("cntn2-57")
        pages[0] = pages[0].replace("AB_3740901", "AB-3740901")
        with self.assertRaises(DatasheetParseError) as raised:
            parse("cntn2-57", pages)
        self.assertIn("RRID", str(raised.exception))

    def test_a_datasheet_with_no_applications_table_is_refused(self):
        pages = load_pages("cntn2-57")
        pages[0] = pages[0].replace("IPI Tested Applications", "Assays We Ran")
        with self.assertRaises(DatasheetParseError) as raised:
            parse("cntn2-57", pages)
        self.assertIn("IPI Tested Applications", str(raised.exception))

    def test_no_pages_is_refused_rather_than_returning_an_empty_record(self):
        with self.assertRaises(DatasheetParseError):
            parse("cntn2-57", [])


if __name__ == "__main__":
    unittest.main()
