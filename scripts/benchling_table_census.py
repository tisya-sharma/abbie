#!/usr/bin/env python3
"""Count rows in every warehouse table without returning record values."""

from __future__ import annotations

import os
from pathlib import Path

from benchling_schema_audit import (
    REPOSITORY_ROOT,
    assert_read_only,
    connection_environment,
    run_psql,
)


SCHEMA_PATH = REPOSITORY_ROOT / "schema-audit" / "warehouse-schema.tsv"
OUTPUT_PATH = REPOSITORY_ROOT / "schema-audit" / "table-census.tsv"
BATCH_SIZE = 40


def table_names() -> list[tuple[str, str]]:
    """Read distinct schema/table pairs from the saved schema audit."""
    if not SCHEMA_PATH.is_file():
        raise SystemExit(
            f"{SCHEMA_PATH} not found. Run benchling_schema_audit.py first."
        )

    seen: set[tuple[str, str]] = set()
    for line in SCHEMA_PATH.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        seen.add((fields[0], fields[1]))
    return sorted(seen)


def batch_query(batch: list[tuple[str, str]]) -> str:
    """Build one UNION ALL counting each table in the batch."""
    selects = []
    for schema, table in batch:
        label = f"{schema}.{table}".replace("'", "''")
        selects.append(
            f"SELECT '{label}' AS relation, count(*)::bigint AS rows "
            f'FROM "{schema}"."{table}"'
        )
    return "\nUNION ALL\n".join(selects) + ";"


def main() -> None:
    environment = connection_environment()
    assert_read_only(environment)

    tables = table_names()
    results: list[str] = []
    failures: list[str] = []

    for start in range(0, len(tables), BATCH_SIZE):
        batch = tables[start : start + BATCH_SIZE]
        try:
            output = run_psql(["-F", "\t", "-c", batch_query(batch)], environment)
        except SystemExit:
            # A batch fails as a unit, so fall back to counting each table alone
            # to isolate the unreadable ones rather than losing the whole batch.
            for schema, table in batch:
                try:
                    output = run_psql(
                        ["-F", "\t", "-c", batch_query([(schema, table)])],
                        environment,
                    )
                except SystemExit:
                    failures.append(f"{schema}.{table}")
                    continue
                results.append(output)
        else:
            results.append(output)

        print(f"Counted {min(start + BATCH_SIZE, len(tables))}/{len(tables)} tables")

    rows = [line for chunk in results for line in chunk.splitlines() if line.strip()]
    rows.sort(key=lambda line: -int(line.split("\t")[1]))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8")
    os.chmod(OUTPUT_PATH, 0o600)

    nonempty = sum(1 for line in rows if int(line.split("\t")[1]) > 0)
    print(f"\nSaved {len(rows)} table counts to {OUTPUT_PATH}")
    print(f"{nonempty} tables hold rows; {len(rows) - nonempty} are empty")
    if failures:
        print(f"{len(failures)} tables could not be read: {', '.join(failures[:10])}")


if __name__ == "__main__":
    main()
