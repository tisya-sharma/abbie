"""Fetching a product's datasheet PDF and turning it into page text.

How the PDF is reached, established by probing all 94 published products rather
than assumed: a product permalink is not a page, it is a redirect. Products
that have a datasheet answer `301` with a `Location` pointing at the PDF under
`/wp-content/uploads/<year>/<month>/`, and products that do not answer `200`
with the ordinary storefront page. Nothing in the REST record carries the PDF
URL, and the upload year and month are not derivable from the product, so
following the permalink is the only discovery mechanism there is.

That makes the HTML case meaningful rather than a fetch failure: a product
whose permalink does not redirect has no published datasheet at all, which is a
fact about the catalog worth reporting and not an error worth retrying.

One request per product, with redirects followed, because the destination is
either the bytes we came for or the answer that there are none.
"""

from __future__ import annotations

from io import BytesIO
from typing import NamedTuple

import httpx
from pypdf import PdfReader
from pypdf.errors import DependencyError, PdfReadError

from packages.catalog.index import REQUEST_TIMEOUT_SECONDS, USER_AGENT

PDF_MAGIC = b"%PDF-"

PDF_CONTENT_TYPE = "application/pdf"

HTML_CONTENT_TYPE = "text/html"

NO_DATASHEET_REASON = (
    "product permalink serves the storefront page, no datasheet PDF is published"
)


class DatasheetFetchError(RuntimeError):
    """The product permalink could not be reached at all."""


class DatasheetExtractError(RuntimeError):
    """Bytes arrived but no readable text came out of them."""


class FetchedDatasheet(NamedTuple):
    """What following one product permalink produced.

    Either `content` and `pdf_url` are set, or `reason` is. The absent-datasheet
    case is modeled here rather than raised so a caller counting the catalog can
    tell "no datasheet" apart from "the fetch broke".
    """

    pdf_url: str | None
    content: bytes | None
    reason: str | None


def classify_destination(
    final_url: str, content_type: str, content: bytes
) -> FetchedDatasheet:
    """Decide what the permalink actually served.

    Both the declared content type and the file's own magic bytes have to agree
    before the response is treated as a datasheet. A misconfigured upload that
    serves HTML with a PDF content type would otherwise reach the extractor and
    fail there with a much less useful message.
    """
    declared = content_type.split(";")[0].strip().casefold()
    if declared == PDF_CONTENT_TYPE:
        if not content.startswith(PDF_MAGIC):
            return FetchedDatasheet(
                None, None, f"{final_url} declared {PDF_CONTENT_TYPE} but is not a PDF"
            )
        return FetchedDatasheet(final_url, content, None)
    if declared == HTML_CONTENT_TYPE:
        return FetchedDatasheet(None, None, NO_DATASHEET_REASON)
    return FetchedDatasheet(
        None, None, f"{final_url} served unexpected content type {declared!r}"
    )


def fetch_datasheet(permalink: str) -> FetchedDatasheet:
    """Follow one product permalink and report what is at the end of it."""
    try:
        response = httpx.get(
            permalink,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise DatasheetFetchError(
            f"{permalink} could not be fetched: {error}"
        ) from error

    return classify_destination(
        str(response.url), response.headers.get("content-type", ""), response.content
    )


def extract_pages(content: bytes) -> list[str]:
    """Extract per-page text from datasheet bytes.

    Page text is kept separate rather than concatenated because the identifier
    printed in every page header is the cheapest available check that the pages
    belong to one document, and joining them first throws that away.
    """
    try:
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except (PdfReadError, DependencyError) as error:
        raise DatasheetExtractError(f"PDF could not be read: {error}") from error

    if not pages:
        raise DatasheetExtractError("PDF carries no pages")
    if not pages[0].strip():
        raise DatasheetExtractError(
            "page 1 yielded no text, which is what a scanned or image-only"
            " datasheet looks like"
        )
    return pages
