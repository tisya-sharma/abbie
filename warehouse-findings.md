# Benchling Warehouse: Audit Findings

What the warehouse actually contains, as facts. Conclusions drawn from these facts live in
[roadmap.md](roadmap.md) and [architecture.md](architecture.md) — this file records the
measurements so that when a conclusion changes, the evidence behind it does not have to be
re-derived.

Audited August 7, 2026, read-only, aggregate counts only. No record values were read.
Reproduce with `scripts/benchling_table_census.py` and `scripts/benchling_validation_status.py`.

## Coverage

513 relations counted across the `protein_innov` and `acl` schemas — every table, not a sample.
242 hold zero rows.

This supersedes an earlier audit that queried 14 hand-picked tables. Several of those names came
back empty and were read as "the data does not exist." They were the wrong names.

## Where each IPI-CHR-001 assay actually lives

The `*_ab_characterization` tables are empty shells. The real data sits under other names.

| Assay | Empty table | Populated table | Rows |
|---|---|---|---|
| SEC | `sec_ab_characterization` | `sec_results$raw` | 18,792 |
| SEC | | `ab_sec$raw` | 14,897 |
| Titer | `valita_ab_characterization` | `antibody_valitatiter$raw` | 16,953 |
| Polyreactivity | `psr_ab_characterization` | `antibody_psr$raw` | 16,854 |
| Cell Display | `cell_display_ab_characterization` | `new_cell_display_results$raw` | 16,075 |
| Intact mass | `mass_spectrometry_antibody_intact_mass` | `..._intact_mass$raw` | 2,572 |
| SPR | `antibody_spr_result` | `antibody_spr_result_multi` | 55,526 |
| BLI | — | `..._bli_result$raw` | 4,403 |

Every assay IPI-CHR-001 describes as universal has data behind it.

## Application-level readout evidence

| Application | Table | Rows |
|---|---|---|
| Immunofluorescence | `if_screening$raw` | 57,453 |
| Flow cytometry | `antibody_facs_summary_result$raw` | 24,875 |
| Flow cytometry | `population_flow_cytometry$raw` | 9,842 |
| Immunofluorescence, 40x | `if_40x$raw` | 45 |
| Western blot | `western_blots$raw` | 0 |
| ELISA, IHC, immunoprecipitation | no table exists | — |

IF and flow carry substantial evidence. Western blot has a table with no rows. ELISA, IHC, and
immunoprecipitation have no table anywhere in the schema — a full-text search of all 513 relation
names returns zero matches.

## Identity and target

| Table | Rows |
|---|---|
| `antibody_lot_registry` | 20,905 |
| `ab_prod_design_variant_registry` | 19,297 |
| `target` | 1,101 |
| `entity_alias` | 197 |

Of the design variants, 55 carry both an RRID and an Addgene number — the natural pilot set for a
publication manifest. Of the targets, 1,047 carry a UniProt identifier, and the table also holds
`gene_name`, `hgnc_id`, `mgi_id`, `approved_symbol_hgnc`, `approved_symbol_mgi`, `ortholog`, and
`protein_families`. Most of the target-normalization vocabulary already exists.

## `antibody_tier` is populated

`antibody_tier$raw` holds **7,303 rows**, with columns `antibody_id` and `tier`. Never queried by
the earlier audit and absent from every planning document until now.

The distribution of `tier` values is still unknown — the status script grouped on the non-raw view,
which is empty, so it returned nothing. Outstanding:

```sql
SELECT tier, count(*) FROM protein_innov."antibody_tier$raw" GROUP BY 1 ORDER BY 2 DESC;
```

## `validation_status$` is not a scientific signal

Distribution across every table carrying the column:

| Value | Rows |
|---|---|
| VALID | 276,603 |
| PASSED | 207,370 |
| (null) | 3,379 |
| FAILED | 19 |

Nineteen FAILED rows in roughly 484,000. This is Benchling's **schema-conformance** flag — it
records whether a row matches its schema definition, not whether a result is scientifically sound.
No quality or release logic should be built on it.

## Why default views are empty while raw tables hold rows

37 tables have a populated `$raw` table and an empty non-raw view. Two distinct causes:

**Some have a `_multi` sibling** that carries the non-raw rows, because the schema produces
multiple rows per run. The base name is empty by design.

| Family | base | `_multi` | `$raw` |
|---|---|---|---|
| `antibody_spr_result` | 0 | 55,526 | 52,375 |
| `mass_spectrometry_antibody_intact_mass` | 0 | 2,491 | 2,572 |
| `v5_titration_results` | 0 | 1,212 | 606 |

**The rest are genuinely empty**, including `if_screening` (57,453 raw), FACS (24,875 raw), and
`antibody_tier` (7,303 raw). These results were created outside Benchling's Notebook Entry flow, so
they exist only in raw. Only **4 entries** in the entire tenant have ever completed review, against
4,675 entries total.

**Consequence: there is no reviewed-versus-unreviewed signal in the warehouse, and none is coming.**
IPI does not use Benchling's review pipeline. The raw tables are the operational source of truth.
The approval manifest described in [roadmap.md](roadmap.md) Stage 2 is therefore not a workaround
for a missing flag — it is the review gate itself.

## Publication state

`bnch$publishing_record$alpha` holds zero rows. Benchling's publishing feature has never been
enabled on this tenant, so nothing in the warehouse records which records IPI considers public.
The 55 design variants with RRIDs and Addgene numbers are public by virtue of Addgene distribution,
but the warehouse does not know that.

## Personally identifiable data

`user`, `team`, `team_member`, `author`, `principal`, `sample_owner`, `request_assignee`, and
`entry_auditor` exist and carry staff names and email addresses. None may reach the public extract.
The column allowlist described in [architecture.md](architecture.md) is what enforces this.

## Open measurements

1. The distribution of `antibody_tier.tier` — query above.
2. Whether the SEC, Cell Display, PSR, and titer tables join cleanly to `antibody_lot_registry`
   and `ab_prod_design_variant_registry`, and on which columns.
3. Whether `if_screening` carries a paralog or cross-reactivity field usable as Selectivity
   evidence, or only Readout.
