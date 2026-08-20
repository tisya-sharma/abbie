"""Unit tests for datasheet resolution and text extraction. No key, no network:

    python3 -m unittest packages.catalog.test_datasheet

The extraction tests build a PDF in memory with fpdf2, which the repository
already depends on for the bench checklist. That keeps a real PDF in the loop
without committing a multi-megabyte one or reaching for the wire.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from fpdf import FPDF

from packages.catalog.datasheet import (
    DatasheetExtractError,
    classify_destination,
    extract_pages,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Same rule packages/antibody holds itself to. The ingest is a batch job today
# and a scheduled Cloud Run job later, and neither should be able to grow a
# web framework by accident. httpx is allowed: this package is the one part of
# the system whose job is to make outbound requests.
FORBIDDEN_IMPORTS = ("fastapi", "fastmcp", "starlette", "openai", "slack_bolt")

PDF_URL = (
    "https://proteininnovation.org/wp-content/uploads/2026/05/"
    "IPI-CNTN2.57-Datasheet.pdf"
)

PRODUCT_URL = "https://proteininnovation.org/product/anti-integrin-alpha-l-ipi-ts2-4/"


def build_pdf(*page_texts: str) -> bytes:
    """Build a PDF in memory, one page per argument. An empty page stays empty."""
    document = FPDF()
    for text in page_texts:
        document.add_page()
        document.set_font("helvetica", size=12)
        if text:
            document.cell(text=text)
    return bytes(document.output())


class TransportFreedomTests(unittest.TestCase):
    def test_the_ingest_imports_no_web_framework(self):
        script = (
            "import sys; import packages.catalog.ingest; "
            f"print(','.join(m for m in {FORBIDDEN_IMPORTS!r} if m in sys.modules))"
        )
        found = subprocess.run(
            [sys.executable, "-c", script],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(found, "")


class ClassifyDestinationTests(unittest.TestCase):
    def test_a_pdf_destination_yields_its_bytes(self):
        content = build_pdf("datasheet")
        fetched = classify_destination(PDF_URL, "application/pdf", content)
        self.assertEqual(fetched.pdf_url, PDF_URL)
        self.assertEqual(fetched.content, content)
        self.assertIsNone(fetched.reason)

    def test_a_product_page_that_does_not_redirect_means_no_datasheet(self):
        """Reported, not raised. Some products are sold with no published
        datasheet at all, which is a fact about the catalog rather than a
        failure of the fetch."""
        fetched = classify_destination(
            PRODUCT_URL, "text/html; charset=UTF-8", b"<!DOCTYPE html>"
        )
        self.assertIsNone(fetched.pdf_url)
        self.assertIsNone(fetched.content)
        self.assertIn("no datasheet", fetched.reason)

    def test_html_served_under_a_pdf_content_type_is_not_treated_as_a_datasheet(self):
        fetched = classify_destination(PDF_URL, "application/pdf", b"<!DOCTYPE html>")
        self.assertIsNone(fetched.content)
        self.assertIn("is not a PDF", fetched.reason)

    def test_an_unexpected_content_type_is_reported_with_the_type(self):
        fetched = classify_destination(PDF_URL, "application/zip", b"PK\x03\x04")
        self.assertIsNone(fetched.content)
        self.assertIn("application/zip", fetched.reason)


class ExtractPagesTests(unittest.TestCase):
    def test_pages_come_back_separately_and_in_order(self):
        pages = extract_pages(build_pdf("first page", "second page"))
        self.assertEqual(len(pages), 2)
        self.assertIn("first page", pages[0])
        self.assertIn("second page", pages[1])

    def test_bytes_that_are_not_a_pdf_raise_rather_than_return_nothing(self):
        with self.assertRaises(DatasheetExtractError):
            extract_pages(b"not a pdf at all")

    def test_a_first_page_with_no_text_is_an_error(self):
        """What a scanned datasheet looks like: pages, but nothing to read."""
        with self.assertRaises(DatasheetExtractError) as raised:
            extract_pages(build_pdf(""))
        self.assertIn("no text", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
