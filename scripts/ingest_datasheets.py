#!/usr/bin/env python3
"""Run the published-datasheet ingest and write the extract to disk.

Reads IPI's public website and nothing else. No key, no credential, no
warehouse: the site is the release gate, so a product page that exists is a
product the public can already see.

    python3 scripts/ingest_datasheets.py

Writes one JSON file per run under packages/catalog/extract/, which is
gitignored the way packages/eval/results/ is, and prints the accounting: what
parsed, what has no datasheet, and what failed with the reason it failed.

There is no database here on purpose. The roadmap puts Abbie's Postgres on
Cloud SQL at Stage 2, and the seam for it is the JSON this writes: loading a
run into a table is one function that reads this file, and nothing in
packages/catalog has to change to gain one.

Exit status is 0 whenever the ingest ran, including when datasheets failed to
parse. Failures are a fact about the catalog that this script exists to report,
not a broken job, and a scheduled run that goes red on them trains everyone to
ignore it. Only an unreadable index exits nonzero, because that is the case
where the report itself is missing.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from packages.catalog.index import CatalogIndexError
from packages.catalog.ingest import ingest_catalog
from packages.catalog.models import IngestResult

EXTRACT_DIR = REPO_ROOT / "packages" / "catalog" / "extract"


def write_extract(result: IngestResult) -> Path:
    """Write one run to a timestamped file and return where it went."""
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = result.built_at.replace(":", "").replace("-", "").replace("+0000", "Z")
    destination = EXTRACT_DIR / f"catalog-{stamp}.json"
    destination.write_text(result.model_dump_json(indent=2) + "\n")
    return destination


def report(result: IngestResult) -> None:
    print(f"{result.products_indexed} published products in the index")
    print(f"{len(result.records)} parsed")
    print(f"{len(result.skipped)} without a published datasheet")
    print(f"{len(result.failures)} failed")

    if result.failures:
        print("\nfailures")
        for failure in result.failures:
            print(f"  {failure.slug} [{failure.stage}]")
            print(f"       {failure.reason}")

    if result.skipped:
        print("\nno datasheet")
        for skipped in result.skipped:
            print(f"  {skipped.slug}")


def main() -> int:
    # pypdf warns about malformed cross-reference entries on most of these
    # files and recovers from all of them. Left at warning level it buries the
    # accounting under several hundred lines that need no action.
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    try:
        result = ingest_catalog()
    except CatalogIndexError as error:
        print(f"index could not be read: {error}", file=sys.stderr)
        return 1

    destination = write_extract(result)
    report(result)
    print(f"\nwritten to {destination.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
