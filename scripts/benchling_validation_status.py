#!/usr/bin/env python3
"""Break down validation_status$ per table without returning record values.

Answers why Benchling's default views are empty while the matching $raw tables hold
rows. Benchling excludes rows from a default view based on their validation state, so
the distribution of validation_status$ across the raw tables is what explains the gap.
A table holding no rows contributes nothing to the output, so the result is the set of
tables that actually carry data, each with its status breakdown.

Also reports the distribution of antibody_tier.tier, which the earlier aggregate audit
never queried and which is the likeliest home for an existing IPI-CHR-001 grading.
"""

from __future__ import annotations

import os

from benchling_schema_audit import (
    REPOSITORY_ROOT,
    assert_read_only,
    connection_environment,
    run_psql,
)


SCHEMA_PATH = REPOSITORY_ROOT / "schema-audit" / "warehouse-schema.tsv"
OUTPUT_PATH = REPOSITORY_ROOT / "schema-audit" / "validation-status.tsv"
STATUS_COLUMN = "validation_status$"
BATCH_SIZE = 30


def tables_with_column(column: str) -> list[tuple[str, str]]:
    """Return schema/table pairs that carry the given column, from the saved audit."""
    if not SCHEMA_PATH.is_file():
        raise SystemExit(
            f"{SCHEMA_PATH} not found. Run benchling_schema_audit.py first."
        )

    matches: set[tuple[str, str]] = set()
    for line in SCHEMA_PATH.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) < 4:
            continue
        if fields[3] == column:
            matches.add((fields[0], fields[1]))
    return sorted(matches)


def distribution_select(schema: str, table: str, column: str) -> str:
    """Build one grouped count over a single table's status column."""
    label = f"{schema}.{table}".replace("'", "''")
    return (
        f"SELECT '{label}' AS relation, "
        f"coalesce(\"{column}\", '(null)') AS status, "
        f"count(*)::bigint AS rows "
        f'FROM "{schema}"."{table}" '
        f"GROUP BY 2"
    )


def batch_query(batch: list[tuple[str, str]], column: str) -> str:
    """Combine a batch of grouped counts into one statement."""
    selects = [distribution_select(schema, table, column) for schema, table in batch]
    return "\nUNION ALL\n".join(selects) + ";"


def collect(batches: list[list[tuple[str, str]]], column: str, environment: dict[str, str]):
    """Run each batch, falling back to single tables so one failure costs only itself."""
    rows: list[str] = []
    failures: list[str] = []

    for batch in batches:
        try:
            rows.append(run_psql(["-F", "\t", "-c", batch_query(batch, column)], environment))
        except SystemExit:
            for schema, table in batch:
                try:
                    rows.append(
                        run_psql(
                            ["-F", "\t", "-c", batch_query([(schema, table)], column)],
                            environment,
                        )
                    )
                except SystemExit:
                    failures.append(f"{schema}.{table}")
    return rows, failures


def main() -> None:
    environment = connection_environment()
    assert_read_only(environment)

    tables = tables_with_column(STATUS_COLUMN)
    print(f"{len(tables)} tables carry {STATUS_COLUMN}")

    batches = [tables[i : i + BATCH_SIZE] for i in range(0, len(tables), BATCH_SIZE)]
    chunks, failures = collect(batches, STATUS_COLUMN, environment)

    tier_query = (
        "SELECT 'protein_innov.antibody_tier' AS relation, "
        "coalesce(tier, '(null)') AS status, count(*)::bigint AS rows "
        "FROM protein_innov.antibody_tier GROUP BY 2;"
    )
    try:
        chunks.append(run_psql(["-F", "\t", "-c", tier_query], environment))
    except SystemExit:
        failures.append("protein_innov.antibody_tier (tier)")

    lines = [line for chunk in chunks for line in chunk.splitlines() if line.strip()]
    lines.sort(key=lambda line: (line.split("\t")[0], -int(line.split("\t")[2])))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(OUTPUT_PATH, 0o600)

    relations = len({line.split("\t")[0] for line in lines})
    print(f"\nSaved {len(lines)} status counts across {relations} non-empty tables")
    print(f"Output: {OUTPUT_PATH}")
    if failures:
        print(f"{len(failures)} tables could not be read: {', '.join(failures[:10])}")


if __name__ == "__main__":
    main()
