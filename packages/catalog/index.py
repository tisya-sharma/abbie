"""Enumeration of IPI's published catalog over the site's public WordPress API.

The website is the release gate. An antibody with a published product page is
public by definition, so the index that decides what Abbie may know about is the
same list a visitor can browse, and nothing here needs a credential.

The REST collection is used rather than the storefront HTML because it is the
only surface that reports `modified` per product. Change detection off a
rendered page means diffing markup, which changes when the theme does.

WordPress caps `per_page` at 100 and reports `X-WP-Total` and `X-WP-TotalPages`
in headers, so the page count is read from the response rather than guessed by
requesting until one comes back empty. Asking past the last page returns 400,
not an empty list, which is what makes the guessed version fail in production
on the day the catalog lands exactly on a page boundary.

The HTTP call sits behind a reader function so the pagination loop can be
tested without a network. That seam exists for the tests and for nothing else.
"""

from __future__ import annotations

import html
from collections.abc import Callable
from typing import Any, NamedTuple

import httpx

from packages.catalog.models import ProductIndexEntry

CATALOG_ENDPOINT = "https://proteininnovation.org/wp-json/wp/v2/product"

# WordPress rejects anything larger with a 400 rather than clamping.
MAX_PER_PAGE = 100

PUBLISHED_STATUS = "publish"

REQUEST_TIMEOUT_SECONDS = 30.0

# Identifies the caller in IPI's own access logs. A bare httpx default is
# indistinguishable from a scraper to whoever is reading them.
USER_AGENT = "abbie-catalog-ingest/0.1 (+https://proteininnovation.org)"


class CatalogIndexError(RuntimeError):
    """The index could not be read, or came back in a shape worth refusing."""


class IndexPage(NamedTuple):
    """One page of the product collection, with the totals its headers carried."""

    entries: list[ProductIndexEntry]
    total_products: int
    total_pages: int


PageReader = Callable[[int, int], IndexPage]


def entries_from_payload(payload: Any) -> list[ProductIndexEntry]:
    """Turn one decoded REST page into typed entries, refusing anything odd.

    Non-published records are rejected rather than filtered. The request already
    asks for published products only, so one arriving anyway means the query and
    the response disagree, and quietly dropping it would hide that.
    """
    if not isinstance(payload, list):
        raise CatalogIndexError(
            f"expected a list of products, got {type(payload).__name__}"
        )

    entries: list[ProductIndexEntry] = []
    for position, item in enumerate(payload):
        if not isinstance(item, dict):
            raise CatalogIndexError(f"product at position {position} is not an object")
        status = item.get("status")
        if status != PUBLISHED_STATUS:
            raise CatalogIndexError(
                f"product {item.get('slug', position)!r} has status {status!r},"
                f" expected {PUBLISHED_STATUS!r}"
            )
        title = item.get("title")
        if not isinstance(title, dict) or not title.get("rendered"):
            raise CatalogIndexError(
                f"product {item.get('slug', position)!r} has no title"
            )
        wanted = ("id", "slug", "link", "modified")
        missing = [key for key in wanted if not item.get(key)]
        if missing:
            raise CatalogIndexError(
                f"product {item.get('slug', position)!r} is missing"
                f" {', '.join(missing)}"
            )
        entries.append(
            ProductIndexEntry(
                product_id=int(item["id"]),
                slug=str(item["slug"]),
                # Titles arrive HTML-escaped, and a clone name in brackets is
                # compared against the datasheet later, so decode once here.
                title=html.unescape(str(title["rendered"])).strip(),
                permalink=str(item["link"]),
                modified=str(item["modified"]),
            )
        )
    return entries


def read_page_over_http(page: int, per_page: int) -> IndexPage:
    """Fetch one page of the published product collection."""
    try:
        response = httpx.get(
            CATALOG_ENDPOINT,
            params={
                "per_page": per_page,
                "page": page,
                "status": PUBLISHED_STATUS,
                "orderby": "id",
                "order": "asc",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as error:
        raise CatalogIndexError(
            f"index page {page} could not be read: {error}"
        ) from error
    except ValueError as error:
        raise CatalogIndexError(
            f"index page {page} was not valid JSON: {error}"
        ) from error

    return IndexPage(
        entries=entries_from_payload(payload),
        total_products=_header_count(response.headers, "X-WP-Total"),
        total_pages=_header_count(response.headers, "X-WP-TotalPages"),
    )


def _header_count(headers: httpx.Headers, name: str) -> int:
    raw = headers.get(name)
    if raw is None:
        raise CatalogIndexError(f"response carried no {name} header")
    try:
        return int(raw)
    except ValueError as error:
        raise CatalogIndexError(f"{name} was {raw!r}, not a count") from error


def fetch_index(
    read_page: PageReader = read_page_over_http,
    per_page: int = MAX_PER_PAGE,
) -> list[ProductIndexEntry]:
    """Enumerate every published product, following the reported page count.

    Entries are deduplicated by product id. Paging a collection that is being
    edited can serve the same record twice, and a duplicate here would become a
    duplicate antibody in the extract.
    """
    if not 1 <= per_page <= MAX_PER_PAGE:
        raise CatalogIndexError(
            f"per_page must be between 1 and {MAX_PER_PAGE}, got {per_page}"
        )

    first = read_page(1, per_page)
    by_id: dict[int, ProductIndexEntry] = {
        entry.product_id: entry for entry in first.entries
    }

    for page in range(2, first.total_pages + 1):
        for entry in read_page(page, per_page).entries:
            by_id[entry.product_id] = entry

    collected = list(by_id.values())
    if len(collected) != first.total_products:
        raise CatalogIndexError(
            f"index reported {first.total_products} products"
            f" but {len(collected)} were read"
        )
    return collected
