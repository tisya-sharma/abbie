"""Unit tests for catalog enumeration. No key and no network:

    python3 -m unittest packages.catalog.test_index

The pagination loop is driven through the reader seam with canned pages, which
is the whole reason that seam exists. Nothing here opens a socket.
"""

from __future__ import annotations

import unittest

from packages.catalog.index import (
    CatalogIndexError,
    IndexPage,
    entries_from_payload,
    fetch_index,
)


def product(product_id: int, *, status: str = "publish") -> dict:
    return {
        "id": product_id,
        "slug": f"anti-example-{product_id}",
        "title": {"rendered": f"Anti-Example [IPI-EX.{product_id}]"},
        "link": f"https://proteininnovation.org/product/anti-example-{product_id}/",
        "status": status,
        "modified": "2026-08-17T13:26:06",
    }


class PaginationTests(unittest.TestCase):
    def test_every_page_the_headers_promise_is_read(self):
        pages = {
            1: [product(1), product(2)],
            2: [product(3), product(4)],
            3: [product(5)],
        }
        asked: list[int] = []

        def read_page(page: int, per_page: int) -> IndexPage:
            asked.append(page)
            return IndexPage(
                entries=entries_from_payload(pages[page]),
                total_products=5,
                total_pages=3,
            )

        entries = fetch_index(read_page=read_page, per_page=2)
        self.assertEqual(asked, [1, 2, 3])
        self.assertEqual([entry.product_id for entry in entries], [1, 2, 3, 4, 5])

    def test_a_single_page_catalog_asks_for_nothing_further(self):
        asked: list[int] = []

        def read_page(page: int, per_page: int) -> IndexPage:
            asked.append(page)
            return IndexPage(
                entries=entries_from_payload([product(1)]),
                total_products=1,
                total_pages=1,
            )

        self.assertEqual(len(fetch_index(read_page=read_page)), 1)
        self.assertEqual(asked, [1])

    def test_a_product_served_on_two_pages_is_counted_once(self):
        """Paging a collection being edited can repeat a record across pages."""
        pages = {1: [product(1), product(2)], 2: [product(2), product(3)]}

        def read_page(page: int, per_page: int) -> IndexPage:
            return IndexPage(
                entries=entries_from_payload(pages[page]),
                total_products=3,
                total_pages=2,
            )

        self.assertEqual(
            [e.product_id for e in fetch_index(read_page=read_page, per_page=2)],
            [1, 2, 3],
        )

    def test_reading_fewer_products_than_promised_is_an_error(self):
        """A page that comes back short is data loss, not a smaller catalog."""

        def read_page(page: int, per_page: int) -> IndexPage:
            return IndexPage(
                entries=entries_from_payload([product(1)]),
                total_products=9,
                total_pages=1,
            )

        with self.assertRaises(CatalogIndexError) as raised:
            fetch_index(read_page=read_page)
        self.assertIn("9 products", str(raised.exception))

    def test_an_out_of_range_page_size_is_refused(self):
        with self.assertRaises(CatalogIndexError):
            fetch_index(
                read_page=lambda page, per_page: IndexPage([], 0, 0), per_page=500
            )


class PayloadTests(unittest.TestCase):
    def test_titles_arrive_with_entities_decoded(self):
        raw = product(1)
        raw["title"]["rendered"] = "Anti-Integrin alpha 5 &amp; beta 1 [IPI-EX.1]"
        self.assertEqual(
            entries_from_payload([raw])[0].title,
            "Anti-Integrin alpha 5 & beta 1 [IPI-EX.1]",
        )

    def test_an_unpublished_product_is_refused_rather_than_filtered(self):
        """The request asked for published products, so a draft means the query
        and the response disagree, and dropping it quietly would hide that."""
        with self.assertRaises(CatalogIndexError) as raised:
            entries_from_payload([product(1, status="draft")])
        self.assertIn("draft", str(raised.exception))

    def test_a_product_missing_its_permalink_is_refused(self):
        raw = product(1)
        del raw["link"]
        with self.assertRaises(CatalogIndexError) as raised:
            entries_from_payload([raw])
        self.assertIn("link", str(raised.exception))

    def test_a_product_with_no_title_is_refused(self):
        raw = product(1)
        raw["title"] = {"rendered": ""}
        with self.assertRaises(CatalogIndexError) as raised:
            entries_from_payload([raw])
        self.assertIn("no title", str(raised.exception))

    def test_an_error_object_instead_of_a_list_is_refused(self):
        with self.assertRaises(CatalogIndexError):
            entries_from_payload({"code": "rest_post_invalid_page_number"})


if __name__ == "__main__":
    unittest.main()
