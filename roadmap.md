# Abbie Roadmap

Working document. This is the operational plan — what gets built, in what order, and what
each stage is waiting on. [architecture.md](architecture.md) holds the architecture and the reasoning behind
it; this file holds the sequence.

Last revised: August 7, 2026.

## What the reference material changed

This roadmap was first drafted from the warehouse audit alone and was wrong in three places.
The internal documents in `answer_references/` correct it:

**IPI has its own validation framework, and it is not the Five Pillars.** The
`4DframeworkAbValid` draft defines four foundational dimensions — Molecular Integrity, Target
Engagement, Selectivity, Experimental Readout — plus the Validation Map, application-specific
Validation Profiles, and Fitness for Purpose. It explicitly departs from IWGAV: knockout,
independent antibodies, and expression correlation are *evidence-strengthening approaches*,
not dimensions. Everything downstream — the corpus, the profile module, the golden set — takes
its shape from this, not from the Five Pillars.

**A release gate exists.** IPI-CHR-001 defines what an antibody must pass before
commercialization through Addgene. The warehouse has no machine-readable flag, which remains
true, but the criteria are written down. The ask to IPI shrinks from "define a publication
policy" to "confirm the Addgene-cleared set is the public set, and confirm the showable fields."

**The rubric largely exists.** IPI-CHR-001 carries real numeric criteria — SEC purity and
retention windows, intact-mass tolerance, titer floor, graded SPR annotations
(Premium/Strong/Weak/Fail) and Cell Display annotations (Binder/Strong/Scale-up). What is
missing is not the rubric but its mapping onto warehouse rows.

**And the missing piece is smaller than it looks, because the framework is qualitative by design.**
The 4D draft states plainly that it does not propose a quantitative scoring system, and that
partial, ambiguous, or conflicting findings should stay visible rather than being concealed within
an aggregate score. So the absence of per-application numeric thresholds is not a gap to be filled
before Stage 3 — it is the framework working as intended. Abbie renders evidence coverage across
the Validation Map, never a single validation figure. See architecture.md, The validation model.

## The constraint that shapes everything below

**The 4D framework is an unpublished draft manuscript.** A public chatbot that explains IPI's
four-dimensional framework before the paper is out would put IPI's own contribution into the
world ahead of its publication. This is not a data-privacy question and the extract boundary
does not address it.

Two consequences, and they need Deb's call before Stage 1 ends:

- The corpus can be **built** on the 4D framework now, and used **internally**, on the same
  footing as any other pre-publication draft.
- **Public** exposure of 4D-specific content — the dimension names as IPI's framework, the
  Validation Map, Validation Profiles — waits for publication, or for explicit clearance.

The fallback if publication is distant: ground the public corpus in already-public IPI content
and general field consensus, and keep the 4D structure as internal scaffolding. That is more
work, so establish which path applies early rather than discovering it at launch.

## The re-phasing, and why

The original phasing bundled everything about IPI's own antibodies into a single "Phase 1 —
IPI collection MVP." That bundle contains three kinds of work with different blockers:

| Work | Blocked on |
|---|---|
| Explaining validation methodology | publication timing only |
| Naming which antibodies IPI has | confirming the Addgene-cleared set is the public set |
| Profiling how validated each one is | mapping IPI-CHR-001 onto warehouse rows |

Bundled, the phase inherited the slowest blocker. Split, each becomes separately answerable —
and none is now the open-ended scientific negotiation the earlier plan assumed.

## Stage 0 — Validation corpus and the application skeleton

**Goal.** A working local Abbie that explains antibody validation and characterization with
citations, and abstains on everything else.

**Deliverables**

- Repo committed and scaffolded to the layout in architecture.md.
- `corpus/concepts/` — 25 to 35 concept files, markdown with provenance frontmatter
  (`id`, `title`, `aliases`, `provenance`, `sources`, `status`, `reviewed_by`, `clearance`,
  `related`). Coverage follows IPI's framework: characterization versus validation; the four
  dimensions individually; the Validation Map, Validation Profile, and Fitness for Purpose;
  the five interpretive principles; the six applications individually; and the distinction
  between validation methods and evidence-strengthening approaches.
- `packages/eval/golden.yaml` — 15 to 20 question / ideal-answer / required-citation triples,
  each tagged `answer`, `abstain`, `refuse`, or `redirect`. All four behaviors are tested; see
  [architecture.md](architecture.md), Guiding principles 3 to 6.
- FastAPI plus Postgres with `pgvector` running locally in Docker.
- Ingest job: markdown to chunks to embeddings, writing `concept` and `concept_chunk`.
- Answer composition: citation rendering, the abstention path, prerequisite expansion in learning
  mode, and follow-up offers generated from `leads_to` edges.
- Per-session `covered` set, so an already-explained concept is not re-offered or re-defined.
- **Prose access ships as a full-context baseline, not retrieval.** The whole corpus is ~9,000
  tokens at full scope, well under 10% of a 128K window, so there is no haystack for retrieval to
  search. Retrieval is built and scored but only merged if it beats the baseline on the golden set.
  See [architecture.md](architecture.md), Two retrieval regimes.
- **Query rewriting ships with retrieval, not with Stage 0.** A follow-up like "what about in mouse
  tissue?" is meaningless as a search string, so retrieval requires rewriting it against the
  conversation first. Under full context there is no query to rewrite. Do not merge retrieval
  without it — a retrieval system missing this degrades on every follow-up turn, and the cause is
  hard to see from the outside.
- Eval harness scoring three configurations — `naive`, `full-context`, `retrieval` — writing
  timestamped results to `packages/eval/results/`. Baselines cannot be reconstructed later, so they
  are captured before anything is built on top of them.
- CI: unit tests, the eval gate, a leak check failing on any RRID, clone-name, or design-ID
  pattern in the corpus, and a clearance check that no concept marked pre-publication can reach
  a public build.
- `apps/mcp/` — an authoring MCP server over the corpus and golden set: `list_concepts(status)`,
  `get_concept(id)`, `find_uncited()`, `run_eval(id)`. It makes corpus authoring and eval
  inspectable from an agent client during the work, and it proves the shared-library packaging
  step that Stage 4's staff server later reuses. No approved data, no deployment.

**Head start.** The kickoff notes already carry Deb's own answers for four questions — what
antibody validation is, and what each of Molecular Integrity, Target Engagement, and
Selectivity mean. Those are authoritative wording from the person who owns the definition, so
they seed both the corpus and the golden set directly. The notes also flag four questions
deliberately left blank: what "functional" means for SPR, what good versus okay versus bad
looks like per application, monoclonal versus polyclonal, and why recombinant antibodies are
better. Those are the first questions to take back to the science team.

**Gate.** Eval green, leak check green, clearance check green, and the bot demonstrably
abstains on every antibody-specific question.

**Blocked on.** Nothing.

**Estimate.** Roughly three weeks at 25 hours per week. Corpus authoring is the long pole.

**Provenance rule.** Every concept declares one of `quoted` (verbatim span plus URL),
`summarized` (own prose, every claim traceable to a cited source), or `ipi-authored` (IPI
stating its own position), plus a `clearance` of `public` or `pre-publication`. Nothing about a
specific antibody enters the corpus — CI enforces that mechanically rather than by memory.

## Stage 1 — Scientific review and first demo

**Goal.** The corpus carries scientist sign-off, and Deb and Travis have seen Abbie work.

**Deliverables**

- Every concept file reviewed and moved from `status: draft` to `status: approved`, with
  `reviewed_by` populated. Review happens as a pull request, so the diff is the audit trail.
- Answers filled in for the four questions the kickoff notes left blank.
- A decision from Deb on 4D publication timing, per the constraint above.
- Demo.

**Gate.** Corpus approved, clearance decision recorded, demo delivered.

**Blocked on.** Roughly an afternoon of scientist time. Keep this ask separate from Stage 3's,
so the small one is not held up by the large one.

**Estimate.** About a week, plus review turnaround.

## Stage 2 — Catalog identity

**Goal.** Abbie can say which antibodies IPI has, and cite them. No validation claims yet.

**Deliverables**

- Written confirmation that antibodies cleared for Addgene distribution under IPI-CHR-001 are
  the public set, and which fields may be shown. This replaces the release-status flag the
  warehouse does not have.
- A publication manifest built from that rule: source record ID, release decision, allowed
  fields, approver, timestamp, policy version, public citation URL. Piloted on the 55 design
  variants already carrying RRIDs and Addgene numbers.
- Extract job: column allowlist, fail-closed, writing into Abbie's own Postgres.
- `get_antibody` and `search_antibodies` over identity fields only.
- Leak tests on every publish, plus a change audit.

**Gate.** Confirmed rule, manifest built, leak tests green, no unapproved record reachable
from the application.

**Blocked on.** One confirmation from IPI, not a policy exercise.

**Estimate.** Roughly a week and a half once confirmed.

**Scope discipline.** Identity only — target, clone name, RRID, Addgene number, isotype,
species, source URL. Assay evidence is Stage 3.

## Stage 3 — Validation Profiles

**Goal.** Defensible application-specific Validation Profiles for the pilot set.

**Deliverables**

- Mapping from IPI-CHR-001's criteria onto warehouse rows: which table and column carries each
  SEC, intact-mass, SPR, Cell Display, polyreactivity, and application-testing result, and how
  each maps onto its dimension.
- Canonical evidence model: one reviewed outcome per antibody, lot, target, application, sample
  type, species, protocol, concentration, version, source.
- Private curation job deriving candidate profiles for scientist review. Only an explicitly
  approved profile crosses into the public database — a derived profile can disclose private
  results even when the underlying rows are withheld.
- Profile rendering in the widget, cited per cell, showing unassessed dimensions as unassessed.

**Gate.** Scientist-reviewed profiles for the pilot antibodies, and the abstention path still
correct outside that set.

**Blocked on.** One thing: locating the release-gate assay data. `sec_ab_characterization`,
`cell_display_ab_characterization`, and `psr_ab_characterization` all audited at zero rows, yet
IPI-CHR-001 says these run on every small-scale antibody, so the data is somewhere the audit did
not look. The table census answers this.

**Not blocked on the application-testing protocols**, contrary to an earlier reading. The SOP does
mark IF, IP, ELISA, and IHC protocols as under development, but the 4D framework is deliberately
qualitative and does not want per-application numeric thresholds — it holds that partial or
conflicting findings should stay visible rather than be absorbed into an aggregate score. A profile
therefore renders evidence coverage per dimension, showing what exists and in what assay and system
context, with gaps shown as gaps. Missing application criteria change what a profile *says*, not
whether it can be built.

**Check `antibody_tier` before assuming this mapping is unbuilt.** The warehouse has a table
keyed `antibody_id` with a single `tier` column. It was never queried — the aggregate audit
covered 14 of 255 tables — and it appears in no document. Given IPI-CHR-001 grades SPR as
Premium/Strong/Weak/Fail and Cell Display as Binder/Strong/Scale-up, a table named
`antibody_tier` is the first place a materialized grading would live. A row count and a
`GROUP BY tier` settle it, and if it is populated, part of Stage 3's mapping already exists.

**Estimate.** Several weeks, gated more on locating and agreeing evidence than on engineering.

**Design constraint.** No single validation score. See architecture.md, Validation Profile module.

## Stage 4 — Deploy and internal pilot

**Goal.** Abbie runs on IPI-owned infrastructure, used by staff before the public sees it.

**Deliverables**

- Terraform for the full footprint, per [hosting-decision.md](hosting-decision.md).
- IPI-owned Google Cloud project, IT holding billing, budget alert on from day one.
- GitHub Actions deploy via Workload Identity Federation.
- Staff surfaces: the MCP server and the Slack app over the shared tool library.
- OpenTelemetry tracing and cost monitoring.

**Gate.** Deployed, staff using it, monitoring and budget alerts live.

**Blocked on.** GCP project ownership and budget sign-off.

**Estimate.** Roughly a week and a half.

**Open thread.** The kickoff notes carry an action item for Travis on AWS access. That is
warehouse access — the Benchling mirror sits on AWS RDS — and not a competing hosting decision.
Worth confirming explicitly, since hosting-decision.md presents Google Cloud as settled and a
stray AWS reference in the notes invites the question.

## Stages 5 to 7 — Third-party coverage, recommendation, public launch

Third-party coverage (RRID, YCharOS, Antibodypedia, CiteAb), experiment-aware recommendation,
then public launch and hardening. Detail in [architecture.md](architecture.md).

**These stages carry the project's real liability, and it is not technical.** They are the first to
make public statements about other companies' products. Three things to settle before building,
not after:

- **Commercial disparagement.** "IPI has no evidence that X was validated for IHC" is defensible.
  "X is poorly validated" is a claim about a competitor's product. The abstention and citation
  discipline already specified is what keeps answers on the first side of that line, and it needs to
  hold under ranking and recommendation too.
- **CiteAb licensing.** The data is commercial and its terms govern display and derived works. A
  ranking is a derived work. Confirm the terms permit it before Stage 5 rather than discovering the
  constraint after the feature exists.
- **Advice as a category.** Deb's capability 3 moves from reporting evidence to recommending action,
  which is a different posture even for research-use-only reagents. Worth an explicit decision on
  how far Abbie goes.

**Scope conflict to resolve with Deb before Stage 6.** Capability 5 asks for commercial antibodies
ranked by validation status. A ranking requires a scalar, and the 4D framework explicitly declines
to produce one — it states that it does not propose a quantitative scoring system and that partial
or conflicting findings should stay visible rather than being concealed within an aggregate score.
Shipping a composite validation score would contradict IPI's own position in a product built to
represent it. The recommended resolution is to rank on a user-chosen axis — "antibodies with
Selectivity evidence in native tissue, ordered by whether Engagement is also established" — which is
orderable and defensible because the user picked the dimension and can see what was not evaluated.
What must not ship is a single validation score collapsing four dimensions into one number. This is
Deb's framework and Deb's stated capability, so it is her call.

## Mapping to the original phases

| This roadmap | architecture.md original | What changed |
|---|---|---|
| Stage 0, Stage 1 | part of Phase 0, plus capabilities #1 and #6 | Promoted to the first shipped thing; reframed on 4D |
| Stage 2 | first half of Phase 1 | Split out; needs a confirmation, not a policy |
| Stage 3 | second half of Phase 1 | Split out; rubric exists, needs mapping |
| Stage 4 | Phase 4 infrastructure, pulled earlier | Deploy once there is something worth deploying |
| Stages 5 to 7 | Phases 2, 3, 4 | Unchanged |

## Standing practices

1. Demo to Deb roughly every two weeks. Working software, not status.
2. GitHub Issues and Projects as the backlog.
3. Definition of done per stage is the gate above.
4. Everything through a pull request, with CI as the reviewer, even working solo.

## Open questions

Needing someone else:

1. **4D publication timing**, and whether pre-publication content may reach the public surface
   (Stage 1). Highest priority — it determines what the first public release can say. Note the
   architecture now makes this a configuration change rather than a rewrite: pre-publication
   concepts live in a separate index, so the decision flips a build target.
2. **Confirmation that the Addgene-cleared set is the public set**, and which fields may be shown
   (Stage 2).
3. **Answers to the four questions the kickoff notes left blank** (Stage 1): what "functional" means
   for SPR, good versus okay versus bad per application, monoclonal versus polyclonal, and why
   recombinant antibodies are preferable.
4. **Which name the fourth dimension takes.** The kickoff notes say "Function in Applications"; the
   manuscript says "Experimental Readout." Abbie will use one in every answer.
5. **Whether capability 5 should produce a ranking at all**, given the framework declines to produce
   a single score (Stage 6). See Stages 5 to 7 above.
6. **Whether staff surfaces may expose unpublished data to OpenAI** (Stage 4). IPI's own OpenAI
   account is the one being used, so this concerns IPI's existing terms rather than a new vendor
   decision.
7. **Third-party licensing terms and budget** (Stage 5), including whether CiteAb's terms permit a
   ranking, which is a derived work.

Ours to answer, and cheap:

8. **The distribution of `antibody_tier.tier`** (Stage 3). The table is populated — 7,303 rows — but
   the value breakdown is not yet measured. One `GROUP BY` settles whether an IPI-CHR-001 grading
   already exists in materialized form.
9. **Whether the release-gate assay tables join cleanly** to `antibody_lot_registry` and
   `ab_prod_design_variant_registry`, and on which columns (Stage 3).

## Resolved by the August 7 warehouse audit

Recorded here rather than deleted, because the earlier answers shaped decisions that are still in
these documents. Measurements are in [warehouse-findings.md](warehouse-findings.md).

- **Where the SEC, Cell Display, and polyreactivity results live.** They exist in volume, under
  different table names than the first audit guessed — `sec_results$raw` (18,792),
  `new_cell_display_results$raw` (16,075), `antibody_psr$raw` (16,854). The `*_ab_characterization`
  tables are empty shells. Stage 3 is no longer blocked on locating this data.
- **Why default views are empty while raw tables hold rows.** Two causes: some families keep their
  non-raw rows in a `_multi` sibling, and the rest were created outside Benchling's Notebook Entry
  flow. `validation_status$` is a schema-conformance flag, not a review signal — 19 FAILED rows in
  roughly 484,000.
- **Whether a reviewed-versus-unreviewed signal exists.** It does not, and none is coming: only 4
  entries in the tenant have ever completed review. The approval manifest is the review gate rather
  than a workaround for a missing one.
- **Whether `antibody_tier` exists.** It does, with 7,303 rows. Its value distribution is question 8
  above.
- **Application-testing protocols for IF, IP, ELISA, IHC.** Still absent, but no longer a blocker —
  the framework is qualitative by design, so profiles render evidence coverage rather than graded
  scores, and a dimension with no numeric criteria renders as evidence-in-context.
