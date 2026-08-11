#!/usr/bin/env python3
"""Measure aggregate chatbot-data readiness without returning record values."""

from __future__ import annotations

import os
from pathlib import Path

from benchling_schema_audit import (
    REPOSITORY_ROOT,
    assert_read_only,
    connection_environment,
    run_psql,
)


OUTPUT_PATH = REPOSITORY_ROOT / "schema-audit" / "aggregate-readiness.tsv"

CANDIDATE_RAW_TABLES = (
    "antibody_bio_layer_interferometry_ab_bli_result$raw",
    "cell_display_ab_characterization$raw",
    "facs_results_mid_scale$raw",
    "flow_yeast_validation$raw",
    "if_40x$raw",
    "if_screening$raw",
    "if_screening_multi$raw",
    "if_summary_multi$raw",
    "population_flow_cytometry$raw",
    "psr_ab_characterization$raw",
    "sec_ab_characterization$raw",
    "valita_ab_characterization$raw",
    "western_blots_plate_abs$raw",
)


QUERY = """
    WITH metrics(metric, value) AS (
        SELECT 'identity.design.total_nonarchived', count(*)::bigint
        FROM protein_innov.ab_prod_design_variant_registry
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'identity.design.with_rrid', count(*)::bigint
        FROM protein_innov.ab_prod_design_variant_registry
        WHERE archived$ IS NOT TRUE AND nullif(rrid, '') IS NOT NULL

        UNION ALL
        SELECT 'identity.design.with_addgene_number', count(*)::bigint
        FROM protein_innov.ab_prod_design_variant_registry
        WHERE archived$ IS NOT TRUE AND addgene_number IS NOT NULL

        UNION ALL
        SELECT 'identity.design.with_clone_name', count(*)::bigint
        FROM protein_innov.ab_prod_design_variant_registry
        WHERE archived$ IS NOT TRUE AND nullif(clone_name_computed, '') IS NOT NULL

        UNION ALL
        SELECT 'identity.design.with_validation_status', count(*)::bigint
        FROM protein_innov.ab_prod_design_variant_registry
        WHERE archived$ IS NOT TRUE AND nullif(validation_status$, '') IS NOT NULL

        UNION ALL
        SELECT 'identity.lot.total_nonarchived', count(*)::bigint
        FROM protein_innov.antibody_lot_registry
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'identity.lot.with_design_variant', count(*)::bigint
        FROM protein_innov.antibody_lot_registry
        WHERE archived$ IS NOT TRUE AND nullif(design_variant, '') IS NOT NULL

        UNION ALL
        SELECT 'identity.lot.with_qc_status', count(*)::bigint
        FROM protein_innov.antibody_lot_registry
        WHERE archived$ IS NOT TRUE AND nullif(qc_status, '') IS NOT NULL

        UNION ALL
        SELECT 'target.total_nonarchived', count(*)::bigint
        FROM protein_innov.target
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'target.with_species', count(*)::bigint
        FROM protein_innov.target
        WHERE archived$ IS NOT TRUE AND nullif(species, '') IS NOT NULL

        UNION ALL
        SELECT 'target.with_uniprot', count(*)::bigint
        FROM protein_innov.target
        WHERE archived$ IS NOT TRUE AND nullif(uniprot_id, '') IS NOT NULL

        UNION ALL
        SELECT 'target.with_pipeline_pillars', count(*)::bigint
        FROM protein_innov.target
        WHERE archived$ IS NOT TRUE AND nullif(pipeline_pillars, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.facs.total_nonarchived', count(*)::bigint
        FROM protein_innov.antibody_facs_summary_result
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'assay.facs.with_antibody_reference', count(*)::bigint
        FROM protein_innov.antibody_facs_summary_result
        WHERE archived$ IS NOT TRUE AND nullif(antibody_name, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.facs.with_validation_status', count(*)::bigint
        FROM protein_innov.antibody_facs_summary_result
        WHERE archived$ IS NOT TRUE AND nullif(validation_status$, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.if.total_nonarchived', count(*)::bigint
        FROM protein_innov.if_summary
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'assay.if.with_antibody_reference', count(*)::bigint
        FROM protein_innov.if_summary
        WHERE archived$ IS NOT TRUE AND nullif(ab_batch_id, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.if.with_selectivity', count(*)::bigint
        FROM protein_innov.if_summary
        WHERE archived$ IS NOT TRUE AND nullif(selectivity, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.western_blot.total_nonarchived', count(*)::bigint
        FROM protein_innov.western_blots
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'assay.western_blot.with_antibody_reference', count(*)::bigint
        FROM protein_innov.western_blots
        WHERE archived$ IS NOT TRUE AND nullif(ab_tab_id, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.western_blot.with_result_status', count(*)::bigint
        FROM protein_innov.western_blots
        WHERE archived$ IS NOT TRUE AND nullif(status, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.western_blot.with_image', count(*)::bigint
        FROM protein_innov.western_blots
        WHERE archived$ IS NOT TRUE AND western_blot_image IS NOT NULL

        UNION ALL
        SELECT 'assay.spr.total_nonarchived', count(*)::bigint
        FROM protein_innov.antibody_spr_result
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'assay.spr.with_antibody_reference', count(*)::bigint
        FROM protein_innov.antibody_spr_result
        WHERE archived$ IS NOT TRUE AND nullif(antibody_lot, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.spr.with_kd', count(*)::bigint
        FROM protein_innov.antibody_spr_result
        WHERE archived$ IS NOT TRUE AND kd_m IS NOT NULL

        UNION ALL
        SELECT 'assay.facs.raw.total', count(*)::bigint
        FROM protein_innov."antibody_facs_summary_result$raw"

        UNION ALL
        SELECT 'assay.facs.raw.nonarchived', count(*)::bigint
        FROM protein_innov."antibody_facs_summary_result$raw"
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'assay.facs.raw.with_validation_status', count(*)::bigint
        FROM protein_innov."antibody_facs_summary_result$raw"
        WHERE nullif(validation_status$, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.facs.raw.with_completed_entry_review', count(*)::bigint
        FROM protein_innov."antibody_facs_summary_result$raw" result
        JOIN protein_innov.entry
          ON entry.id = result.entry_id$
        WHERE entry.review_completed_at IS NOT NULL

        UNION ALL
        SELECT 'assay.if.raw.total', count(*)::bigint
        FROM protein_innov."if_summary$raw"

        UNION ALL
        SELECT 'assay.if.raw.nonarchived', count(*)::bigint
        FROM protein_innov."if_summary$raw"
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'assay.if.raw.with_validation_status', count(*)::bigint
        FROM protein_innov."if_summary$raw"
        WHERE nullif(validation_status$, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.if.raw.with_completed_entry_review', count(*)::bigint
        FROM protein_innov."if_summary$raw" result
        JOIN protein_innov.entry
          ON entry.id = result.entry_id$
        WHERE entry.review_completed_at IS NOT NULL

        UNION ALL
        SELECT 'assay.western_blot.raw.total', count(*)::bigint
        FROM protein_innov."western_blots$raw"

        UNION ALL
        SELECT 'assay.western_blot.raw.nonarchived', count(*)::bigint
        FROM protein_innov."western_blots$raw"
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'assay.western_blot.raw.with_validation_status', count(*)::bigint
        FROM protein_innov."western_blots$raw"
        WHERE nullif(validation_status$, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.western_blot.raw.with_completed_entry_review', count(*)::bigint
        FROM protein_innov."western_blots$raw" result
        JOIN protein_innov.entry
          ON entry.id = result.entry_id$
        WHERE entry.review_completed_at IS NOT NULL

        UNION ALL
        SELECT 'assay.spr.raw.total', count(*)::bigint
        FROM protein_innov."antibody_spr_result$raw"

        UNION ALL
        SELECT 'assay.spr.raw.nonarchived', count(*)::bigint
        FROM protein_innov."antibody_spr_result$raw"
        WHERE archived$ IS NOT TRUE

        UNION ALL
        SELECT 'assay.spr.raw.with_validation_status', count(*)::bigint
        FROM protein_innov."antibody_spr_result$raw"
        WHERE nullif(validation_status$, '') IS NOT NULL

        UNION ALL
        SELECT 'assay.spr.raw.with_completed_entry_review', count(*)::bigint
        FROM protein_innov."antibody_spr_result$raw" result
        JOIN protein_innov.entry
          ON entry.id = result.entry_id$
        WHERE entry.review_completed_at IS NOT NULL

        UNION ALL
        SELECT 'publishing.records.total', count(*)::bigint
        FROM protein_innov."bnch$publishing_record$alpha"

        UNION ALL
        SELECT 'publishing.records.currently_published', count(*)::bigint
        FROM protein_innov."bnch$publishing_record$alpha"
        WHERE published_at IS NOT NULL AND unpublished_at IS NULL

        UNION ALL
        SELECT 'publishing.links_to_design_variants', count(*)::bigint
        FROM protein_innov."bnch$publishing_record$alpha" publishing
        JOIN protein_innov.ab_prod_design_variant_registry design
          ON design.id = publishing.publishable_id

        UNION ALL
        SELECT 'publishing.links_to_antibody_lots', count(*)::bigint
        FROM protein_innov."bnch$publishing_record$alpha" publishing
        JOIN protein_innov.antibody_lot_registry lot
          ON lot.id = publishing.publishable_id

        UNION ALL
        SELECT 'publishing.links_to_entries', count(*)::bigint
        FROM protein_innov."bnch$publishing_record$alpha" publishing
        JOIN protein_innov.entry
          ON entry.id = publishing.publishable_id

        UNION ALL
        SELECT 'review.links_to_design_variants', count(*)::bigint
        FROM protein_innov."bnch$review$alpha" review
        JOIN protein_innov.ab_prod_design_variant_registry design
          ON design.id = review.reviewable_id

        UNION ALL
        SELECT 'review.links_to_antibody_lots', count(*)::bigint
        FROM protein_innov."bnch$review$alpha" review
        JOIN protein_innov.antibody_lot_registry lot
          ON lot.id = review.reviewable_id

        UNION ALL
        SELECT 'review.links_to_entries', count(*)::bigint
        FROM protein_innov."bnch$review$alpha" review
        JOIN protein_innov.entry
          ON entry.id = review.reviewable_id
    )
    SELECT metric, value
    FROM metrics
    ORDER BY metric;
"""


def candidate_table_query() -> str:
    statements = []
    for table in CANDIDATE_RAW_TABLES:
        metric = table.removesuffix("$raw")
        statements.append(
            f"SELECT 'candidate.{metric}.raw.total', count(*)::bigint "
            f'FROM protein_innov."{table}"'
        )
    return "\nUNION ALL\n".join(statements) + "\nORDER BY 1;"


def main() -> None:
    environment = connection_environment()
    assert_read_only(environment)
    output = run_psql(["-F", "\t", "-c", QUERY], environment)
    output += run_psql(
        ["-F", "\t", "-c", candidate_table_query()],
        environment,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    os.chmod(OUTPUT_PATH, 0o600)

    metrics = sum(1 for line in output.splitlines() if line.strip())
    print("Connected using a read-only transaction.")
    print(f"Saved {metrics} aggregate readiness metrics to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
