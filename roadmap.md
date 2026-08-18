# Abbie Roadmap

Working document. This is the operational plan — what gets built, in what order, and what
each stage is waiting on. [architecture.md](architecture.md) holds the architecture and the reasoning behind
it; this file holds the sequence.

Last revised: August 17, 2026.

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
commercialization through Addgene. No machine-readable release flag exists at the source — not in
the warehouse and not in the datasheet Airtable — but the criteria are written down. The ask to IPI
has now shrunk twice: first from "define a publication policy" to "confirm the Addgene-cleared set
is the public set, and confirm the showable fields," and then, on August 17, 2026, to the written
record of a confirmation already given plus the showable-field list.

**The rubric largely exists.** IPI-CHR-001 carries real numeric criteria — SEC purity and
retention windows, intact-mass tolerance, titer floor, graded SPR annotations
(Premium/Strong/Weak/Fail) and Cell Display annotations (Binder/Strong/Scale-up). What is
missing is not the rubric but its mapping onto the datasheet Airtable's tables.

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
| Naming which antibodies IPI has | the written record of the confirmed Addgene-cleared set |
| Profiling how validated each one is | mapping IPI-CHR-001 onto the datasheet Airtable |

Bundled, the phase inherited the slowest blocker. Split, each becomes separately answerable —
and none is now the open-ended scientific negotiation the earlier plan assumed.

## From answers to workflows: the agent arc

**The stages below are ordered by content trust. This section orders the same stages by
capability.** They are one plan seen from two ends: Stage 2 is where Abbie may first name an
antibody and also where Abbie first calls a tool, and those are the same event. What the trust
ordering does not say is what Abbie can *do* at each step, so read alone it looks like a plan for a
chatbot that gets progressively better sourced. Abbie today is three deterministic hops — a cheap
router call returning behavior, subject, and form, one composer call with the whole corpus in
context, a leak scan over the result — which is right for explaining a concept and wrong for
carrying a task. What researchers arrive with are tasks: I have this antibody, this application,
this tissue, what do I need to run. A task takes several steps, several sources, and something
remembered between them.

**It reframes the stages, it does not replace them.** Named below are the workflows Abbie should
carry end to end and the five capabilities that carry them — tool use, reflection, planning and
decomposition, multi-agent orchestration, memory and context management — but every gate below
still holds and no capability lands before the data it would act on. Deferred decisions are
re-evaluated here rather than inherited, and where a deferral survives it is restated as an evidence
gate with a named re-open condition, because "not yet, and here is the measurement that changes it"
can be revisited on evidence while a flat no gets revisited on mood.

### The workflows

Each entry is something a researcher is trying to finish rather than something they are trying to
have explained. The stage named is where the workflow lands whole.

**Guided validation planning.** Seeds now, full at Stage 3. The researcher has an antibody and an
experiment in mind and does not know what evidence would make the experiment trustworthy. Abbie asks
for what is missing — target, application, species, sample type, whether the readout is qualitative
or quantitative — walks the four dimensions for that application, and assembles a validation plan
ending in the bench checklist the widget already exports. The capability change is that the
checklist stops being a button the visitor presses afterward and becomes a tool the model invokes
inside the workflow, with the plan as its argument, so the artifact is built out of the reasoning
rather than assembled beside it. The corpus supports the walk today, which is why the seeds ship
now; a plan naming IPI's own antibodies as candidates waits for Stage 3. Exercises planning, tool
use, and session memory.

**Catalog navigation.** Stage 2. "What does IPI have against this target" is answered by
`search_antibodies` and `get_antibody` inside a bounded tool loop rather than by one composed reply
over a static context. It is the first workflow where the model chooses what to fetch, so it is the
one that establishes the tool-loop contract below. Exercises tool use.

**Validation profile reading.** Stage 3. Today every question about a named antibody's validation
status routes to `abstain`, which is correct while there is nothing approved to say. A
`get_validation_profile` tool over the approved profile store converts that abstention into a
grounded answer for the pilot set, with the abstention path unchanged everywhere outside it. The
stakes are higher here than anywhere before it, because the reply is a claim about a specific
reagent, so this is the workload the runtime reflection A/B runs against. Exercises tool use and
reflection.

**Evidence dossier.** Stage 5. The researcher wants everything published about an antibody, not only
what IPI measured. Abbie gathers from the registry tools — RRID, Antibodypedia, CiteAb — and from
the already-designed web-search tool, in parallel rather than in sequence, and synthesizes one cited
dossier saying which source each claim came from and where the sources disagree. Disagreement is the
point: a knockout-controlled western in one paper and a failed IHC in another is more useful than
either fact alone. Exercises tool use and multi-agent orchestration.

**Experiment-aware recommendation.** Stage 6. The full planning workload, and the reason the rest of
the arc exists. The experiment context is decomposed into what it demands of a reagent, candidates
are searched across the IPI catalog and the third-party registries, profiles are read for each
survivor, fitness for purpose is assessed per candidate against the stated application, and a
recommendation is composed with its caveats and its gaps attached. Whether this may produce a
ranking at all is unresolved and is Deb's call — see Stages 5 to 7, and open question 5. Nothing
here resolves it, and the capability work is independent of it: decomposition, parallel search, and
per-candidate assessment are needed whether the output is an ordered list on a user-chosen axis or
an unordered candidate set with its evidence shown. Exercises all five.

**Staff authoring copilot.** Stage 4. The MCP server and the Slack app are listed at Stage 4 as
transport, but the interesting thing about them is that they serve a different role with a different
context. A staff member authoring a concept wants sourcing checks, prerequisite-graph sanity,
coverage gaps against the golden set, and prose matching the voice rules, none of which the public
answerer should ever do. Running the copilot as a separate role, its own instructions and its own
tools over the same tool library, keeps the public answerer's context clean. Exercises multi-agent
orchestration and tool use.

**Returning-researcher continuity.** Infrastructure at Stage 4, payoff at Stage 6. A researcher who
described their organism, applications, and targets last week should not have to describe them
again. An opt-in researcher profile — written only on explicit confirmation, visible and erasable by
its owner — lets a later session resume instead of restart. The store arrives with Stage 4's session
persistence; the payoff is at Stage 6, the workflow with enough setup cost to be worth not paying
twice. Exercises memory.

### Tool use

**Current state: none.** The pipeline is a single composer call, and the widget's checklist export
is a client-side button posting to `/export/checklist`, not something the model can invoke. What
exists is the design: architecture.md already specifies a transport-free tool library under
`packages/antibody`, called in process by the widget and over MCP by staff.

The layer grows per stage rather than arriving at once. Stage 2: `get_antibody` and
`search_antibodies` over identity fields, the loop itself, and web search in log-only mode, which
spends nothing and measures demand. Stage 3: `get_validation_profile` over approved profiles, and
the bench checklist promoted from an export endpoint to a model-invoked tool. Stage 4: web search
staff-only, and the MCP and Slack surfaces over the same library. Stage 5: one registry tool per
third-party source.

**The bounded tool-loop contract supersedes the single-shot composer the day the first tool ships,
and these are its terms.** It runs on LangGraph from that first shipment at Stage 2 — a small
`StateGraph` with a capped tool-execution loop — rather than being hand-rolled now and migrated
later. The contract's terms are unchanged by that choice. The router still runs first and unchanged,
so `refuse` and `abstain` remain deterministic paths that never enter the loop at all. Tool calls
are capped per turn — start at four, raise only on a measured workload that needs more, and a turn
that exhausts its cap returns what it has with the gap stated rather than looping. Every call is a span, so cost and latency stay
readable by the feedback loop. The leak scan runs on the final text exactly as now, which matters
more once tool output is in the context than it did when only the corpus was.

**"Never an agent loop" is scoped, not deleted.** The web-search design says no client-side
tool-runner, no multi-step agent, and no model-directed iteration on a public endpoint, with the
provider running its own bounded search internally. That is a bound on unbounded browsing, and it
still holds. It was never a claim that Abbie may not call a typed tool against IPI's own database
under a per-turn cap, which is a different risk with a different failure mode: bounded, private,
enumerable, and testable. See Web search — designed, not scheduled, below.

### Reflection

**Near-term deliverable, at the Stage 0 and Stage 1 boundary: fill the judge seam.** `score_case` in
`packages/eval/checks.py` already sets `"judge": None`, with a docstring calling it a seam for a
later model-graded pass against the ideal. Filling it means a model-graded comparison of each reply
against that case's authored ideal, flag-gated and cached the way the other eval calls are, so a
re-scored run costs nothing. It lands in the tracked, non-blocking tier and stays there until it has
enough runs behind it for a defensible trigger value, on the rule every tracked metric already
follows: a metric nobody acts on is worse than no metric.

**Runtime critique-and-revise is not assumed, it is scheduled as an experiment.** A second model
pass that critiques and rewrites the draft is the obvious next move and it is not obviously worth
its latency. So it runs as an A/B on the golden set at Stage 3, against the property checks that
already exist, adopted only if the pass-rate lift justifies the added latency and cost. Two things
to pre-register rather than decide while reading the result: the lift has to clear the detection
floor already published for this sample size, near thirteen percentage points on paired flips, or
the run cannot tell adoption from noise, and the latency budget for a streamed first token has to be
stated before the numbers are in. Stage 3 is the right place because it is the first workload where
a wrong answer is a claim about a real reagent.

**The leak scan stays the deterministic last line either way.** A model reviewing its own output is
a quality mechanism, not a safety one, and nothing here moves a safety property behind a model call.

### Planning and decomposition

**The router is already a light planner.** It classifies behavior and question form in one cheap
call, and that classification decides the shape of everything downstream: which prompt, which
prerequisites, whether a procedural first touch withholds its steps. A one-step plan from a fixed
menu is the correct amount of planning for a single-turn answer.

Real multi-step planning arrives with Stage 6 recommendation: decompose the experiment context into
sub-questions, execute them over the tool layer, then compose. The intermediate stages do not need
it. A catalog lookup is a tool call, not a plan, and a profile read is two.

**The orchestration framework is adopted at Stage 2 with the tool loop, not decided at Stage 6.**
LangGraph carries the bounded loop from its first shipment, so Stage 6 is an extension of a graph
already in production rather than an adoption decision taken under deadline. The earlier position —
that a framework whose features go unused is a dependency with no consumer, the same argument that
retired `apps/mcp/` at Stage 0 — held while the graph was a fixed sequence. A capped tool loop is a
cycle, which is the first of the criteria and consumer enough. Those criteria still stand, named so
the decision is read against them rather than against taste: cycles in the graph, conditional
branching on intermediate results, human-in-the-loop pauses needing the run suspended and resumed,
and parallel workers whose results have to be joined. What they now govern is how much of the
framework Stage 6 uses, not whether it enters. The tradeoff stated plainly: a dependency taken
earlier than its full feature set is needed, in exchange for no migration later and for the
checkpointing the deploy target requires anyway — see Memory and context management.

### Multi-agent orchestration

**Adopted where context isolation pays, not as an aesthetic.** Multiple agents cost tokens, latency,
and a new class of failure where two roles disagree. They earn that only when a workload wants a
different context rather than a different paragraph of instructions.

Two places earn it. The staff authoring copilot at Stage 4 runs as a role separate from the public
answerer, with its own instructions and its own tools over the shared library, because its context
includes work in progress the public answerer must never see. Registry gathering in Stages 5 and 6
fans out one worker per source — RRID, Antibodypedia, CiteAb, web search — in parallel behind a
synthesizer that merges and reconciles, because the sources are independent, the latency is additive
in sequence, and one source failing should not take the dossier with it.

**The public question-and-answer path stays a single routed call until a workload demands
otherwise.** The re-open condition is specific: a named workload whose context does not fit
alongside the corpus, or whose failure modes differ in kind from the answerer's rather than in
degree. Until then, splitting the answerer buys latency for nothing.

### Memory and context management

**Session memory today is in-process and does not survive a restart.** The per-session `covered` set
lives in the application process and feedback verdicts live only on traces, so a deploy erases both
and the pilot-era feedback loop reads a signal that keeps disappearing. Stage 4 fixes it: session
persistence in a small managed store, so sessions survive restarts and a feedback verdict joins the
conversation it was given about. **The forcing fact is the deploy target.** Abbie runs on Cloud Run,
which autoscales and scales to zero, so the in-process `SESSIONS` dict cannot survive between two
requests, let alone across two conversations. Session persistence is deploy-blocking at Stage 4, not
an improvement scheduled there. The engine is no longer an open question either: LangGraph's
Postgres checkpointer in the Cloud SQL instance the plan already stands up, which is the same
framework the tool loop has been running on since Stage 2 and the same database the catalog extract
writes into. The shape is what it always was — small and managed, not a second system to operate —
and the opt-in researcher profiles ride it rather than earning a store of their own.

**Context management is the retrieval question, and it moves from a one-time trigger to a standing
cadence.** The full-context baseline won on the golden set and the reasons are recorded under Stage
0. What was wrong was leaving the re-open condition as a single distant number, because a threshold
checked once is a threshold nobody checks. Instead: re-run the retrieval-versus-full-context
comparison on the golden set at every corpus milestone, roughly every thirty added concepts or
whenever assembled context crosses 50k tokens, whichever comes first, measured through
`assemble_context()` and `estimate_tokens()` the way the application measures it. The challenger is
designed now so the switch is an eval result away rather than a rebuild: hybrid retrieval, lexical
and embedding, over concept-level chunks rather than arbitrary spans, with prerequisite closure
preserved, since a retrieved concept has to pull its `requires` closure, which full-context gets for
free and naive top-k silently drops. It has a substrate and a build point now rather than only a
design: `pgvector` in the Cloud SQL instance [hosting-decision.md](hosting-decision.md) already
names, built as a tracked experiment once that database exists at Stage 2 and re-run on the cadence
above. The merge rule does not change: retrieval ships only if it beats the full-context baseline on
the golden set.

**Langfuse activation is immediate, because it is already built.** `packages/telemetry` constructs
its OTLP exporter from `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`, falling back to the default
host, so turning on trace inspection is configuration rather than engineering. That makes it a Stage
1 demo deliverable rather than a Stage 4 one, and it changes what the demo-era feedback loop can
read: traces reviewed after each demo session, with questions the corpus could not answer written up
as golden-set cases first and corpus concepts second. See The feedback loop, specified, which
already describes that cadence and is waiting on somewhere durable to read the traces from.

## Stage 0 — Validation corpus and the application skeleton

**Goal.** A working local Abbie that explains antibody validation and characterization with
citations, and abstains on everything else.

**Deliverables**

- Repo committed and scaffolded to the layout in architecture.md.
- `corpus/concepts/` — 25 to 35 concept files, markdown with provenance frontmatter
  (`id`, `title`, `aliases`, `ask`, `provenance`, `sources`, `status`, `reviewed_by`,
  `clearance`, `level`, `requires`, `leads_to`). Coverage follows IPI's framework: characterization versus validation; the four
  dimensions individually; the Validation Map, Validation Profile, and Fitness for Purpose;
  the five interpretive principles; the six applications individually; and the distinction
  between validation methods and evidence-strengthening approaches.
- `packages/eval/golden.yaml` — 15 to 20 question / ideal-answer / required-citation triples,
  each tagged `answer`, `abstain`, `refuse`, or `redirect`. All four behaviors are tested; see
  [architecture.md](architecture.md), Guiding principles 3 to 6.
- FastAPI, serving the routed pipeline over SSE to a single static page.
- Answer composition: citation rendering, behavior routing with a deterministic refusal and
  abstention layer, prerequisite expansion in learning mode, and follow-up offers generated from
  `leads_to` edges.
- Per-session `covered` set, so an already-explained concept is not re-offered or re-defined.
- **Prose access ships as a full-context baseline, not retrieval.** The whole corpus is ~9,000
  tokens at full scope, well under 10% of a 128K window, so there is no haystack for retrieval to
  search. Retrieval is built and scored but only merged if it beats the baseline on the golden set.
  See [architecture.md](architecture.md), Two retrieval regimes.
- Eval harness scoring `naive`, `full-context`, and `routed`, writing timestamped results to
  `packages/eval/results/`. Baselines cannot be reconstructed later, so they are captured before
  anything is built on top of them.
- CI: unit tests, a leak check failing on any identifier pattern in the corpus, and a clearance
  check that no concept marked pre-publication can reach a public build. The eval is deliberately
  not in CI, because it spends OpenAI credit on every push; it runs deliberately and its result
  json is promoted into the repo as the gate record.

**Four deliverables were superseded, and why.** Recorded rather than deleted, because each was a
reasoned position and the reasoning is what dates.

- **Postgres with `pgvector` in Docker, and the embeddings ingest job.** Both existed to serve
  retrieval. The full-context baseline won, so neither has a consumer. Retrieval over a corpus
  this size cannot improve precision and can lose, because every top-k selection is a chance to
  miss a chunk the answer needed.
- **The `retrieval` eval configuration.** Replaced by `routed`, which is the comparison that
  turned out to matter: behavior routing against a single full-context call.
- **Query rewriting.** It was a precondition on merging retrieval. With no retrieval it has
  nothing to rewrite against. The constraint stands unchanged for whenever retrieval arrives.
- **`apps/mcp/`, the authoring server.** Written to make corpus authoring inspectable from an
  agent client. At seventeen files the corpus is edited directly and the server would be tooling
  for a problem that never appeared. MCP's real consumer is Stage 4's staff surface, serving the
  antibody library to ChatGPT, and that is where it should be built. The Slack app calls the same
  tool library directly, since Slack is not an MCP client.

**Revisiting retrieval is a cadence, not a one-time milestone.** The assembled corpus
is currently ~15,800 tokens across thirty-seven concepts, about 426 tokens each. Measure it the
way the application does — `assemble_context()` through `estimate_tokens()` in
`packages/corpus_loader` — because counting whole files instead sweeps in frontmatter and the
Vancouver source labels and comes out roughly half again too high. Cost and attention dilution
both start to bind somewhere around 100k tokens of prose, which is roughly 240 concepts at that
size. So the outer bound is ~50k tokens, around 120 concepts, which leaves room to
measure before it is needed. An earlier revision of this paragraph put the trigger at 96
concepts on the grounds that concepts had grown denser than the first estimate of 376 tokens each.
They had not: the thirty-one-concept corpus measured 383, essentially that estimate, and the
density claim was an artifact of measuring whole files. As of August 17 the thirty-seven-concept
corpus measures 426, modestly above that estimate, with the fully sourced application concepts
the likely driver. Ingesting IPI publications, protocols, or the product datasheets wholesale,
rather than hand-authoring concepts, crosses that line immediately and is the likelier trigger.
The rule that retrieval must beat the full-context baseline on the golden set does not change.

**What has changed is that the outer bound is no longer the only check.** A number tested once, far
away, is a number nobody tests, so the comparison now runs on a standing cadence — every corpus
milestone, roughly every thirty added concepts, or whenever assembly crosses 50k tokens, whichever
comes first. The challenger design is named rather than left to be invented at the time, and as of
August 17 so is what it runs on: `pgvector` in the Cloud SQL instance from
[hosting-decision.md](hosting-decision.md), built at Stage 2 once that database exists for the
catalog extract. That is not the retired Docker Postgres returning by the back door — the database
is being stood up for the extract either way, so the challenger costs an extension rather than a
system to operate. See From answers to workflows, Memory and context management.

**Head start.** The kickoff notes already carry Deb's own answers for four questions — what
antibody validation is, and what each of Molecular Integrity, Target Engagement, and
Selectivity mean. Those are authoritative wording from the person who owns the definition, so
they seed both the corpus and the golden set directly. The notes also flag four questions
deliberately left blank: what "functional" means for SPR, what good versus okay versus bad
looks like per application, monoclonal versus polyclonal, and why recombinant antibodies are
better. Those are the first questions to take back to the science team.

**Gate.** Eval green, leak check green, clearance check green, and the bot demonstrably
abstains on all enumerated antibody-specific cases.

That last clause used to read "every antibody-specific question," which the golden set cannot
support. Zero failures across 48 cases bounds the true failure rate at roughly 6% by the rule of
three, so "every" claims coverage of a question space the set never sampled. What the gate can
assert is conformance on the cases enumerated in it.

**What "eval green" means.** Left undefined until August 16, which made this gate unrunnable: a
criterion that acquires its meaning after the results are in is not a criterion. It is now three
tiers, pre-registered here rather than decided at the moment of reading a run.

*Blocking, absolute.* The three `abstain` and three `refuse` cases must pass their behavior check
and leak check, on all three trials rather than a majority. That is roughly eighteen assertions.
Deliberately narrow: a zero-tolerance gate's false-block rate compounds with the number of things
it gates, so gating every check on every case would block almost every release on sampling noise
alone. The 22 `redirect` cases sit in the tracked tier instead, because redirect quality is not a
safety property and including it inflates the blocking set twentyfold.

*Blocking, relative.* No regression against the pinned baseline on `answer` cases, read as an
exact McNemar test on paired per-case flips. Publish the detection floor beside the verdict: with
this many cases the test cannot fire below about six discordant pairs all falling one way, near
thirteen percentage points. A green result here means no regression was detected, which at this
sample size is not the same as no regression.

*Tracked, non-blocking.* Em dash count, section labels, word budget, voice, router form accuracy,
citation rate. Reported every run, never blocking. Each needs a named owner and a trigger value or
it should be deleted rather than tracked, because a metric nobody acts on is worse than no metric.

The owner column is provisional. Every row reads the same name because nobody else has been assigned
one yet, and a placeholder naming a real person is the only kind that gets noticed when it is wrong.

| Metric | Latest | Trigger → action | Owner (provisional) |
|---|---|---|---|
| Em dash count | 80.5% | under 90% on two consecutive runs, or any case failing all three trials → corpus prose, not prompt | Tisya (interim) |
| Section labels | 91.5% | under 90% on any run → prompt change | Tisya (interim) |
| Word budget | 95.9% | under 90% on any run → budget change | Tisya (interim) |
| Voice (pooled) | 96.9% | under 95% on two consecutive runs → read the per-check series first | Tisya (interim) |
| Router form accuracy | 81.6% | under 80% on any run, or one form pair missed in 3+ cases → router prompt change | Tisya (interim) |
| Citation rate | 93.9% | under 90% on two consecutive runs → the named missing slugs say corpus or prompt | Tisya (interim) |

Latest is the routed run of August 17, `eval-20260817-192634`. The first three are case-level pass
rates as `scripts/eval_trends.py` reports them; the last three are the summary fields
`voice_pass_rate`, `router.form_accuracy`, and `citation_pass_rate`. A trigger is checked by running
the tool, not by recomputing anything.

**Each threshold sits just under its own series' observed floor**, so it fires on new behavior rather
than on the sampling noise the headline pass rate already carries. Across the eight recorded routed
runs: word budget climbed 44.4 → 76.5 → 88.9 → 88.9 → 94.4 → 94.4 → 95.9 as the budget was tuned, so
90% is under a level held for three runs. Section labels has never gone below 90.0. Router form
accuracy has never left 81.6 to 88.9 across the six runs that measured it, which makes 80% a floor
breach rather than a bad day, and its second condition is already met — conceptual was read as
procedural in three cases in the latest run. Citation rate at a single-run 90% would have fired in
four of six runs and said nothing; two consecutive separates the 88.9 plateau, which was real and was
fixed, from the 93.9 that followed. Voice is the weakest of the six and its trigger admits it: it
pools every check except behavior and citation, so one bad check barely moves it — em dash at 68.6%
coincided with voice at 93.3% — and the only honest action is to go read the per-check series. If
that series stays easier to read than the composite, delete the composite.

**The em dash trigger took the most thought, because the check is the noisiest thing here.** It fails
on 30 of 231 trials in the latest run, 13%, against 6.1% for the next worst, and it is implicated in
three of the four cases that failed on all three trials. Its case-level rate has swung 68.6 → 84.8 →
97.8 → 89.1 → 93.5 → 80.5 while the case pool grew from 35 to 77, so a single-run threshold anywhere
in that band fires on resampling and pool composition rather than on drift. Two consecutive runs
under 90% would have fired once in six, on the 68.6 and 84.8 pair, which is the one stretch that was
genuinely bad. The all-trials condition is separate because a case that fails every trial is not a
sampling result — the model does it every time — so waiting for a second run to act buys nothing.

**Its action is the part worth arguing.** Another prompt paragraph is the lever already pulled: the
system prompt spends a dozen lines on this rule, names both failure shapes, and tells the model to
count before finishing, and the check still fails 13% of trials. What has not been tried is the prose
the model is reading. The 37 concept files carry 65 em dashes between them, so a reply grounded in
three concepts sees roughly five in its context while being told to emit at most one. That is the
next place to look, and it is cheap to test.

Report the coverage figure next to the pass count, as `N of M passing, C of K concepts asserted`.
The two numbers answer different questions and the second is currently the weaker one.

Do not put an aggregate pass rate in a deploy note. At this sample size the interval around it
spans about twenty points, and four runs on an identical case pool have already produced 32, 39,
34 and 39.

**Blocked on.** Nothing.

**Estimate.** Roughly three weeks at 25 hours per week. Corpus authoring is the long pole.

**Provenance rule.** Every concept declares one of `quoted` (verbatim span plus URL),
`summarized` (own prose, every claim traceable to a cited source), or `ipi-authored` (IPI
stating its own position), plus a `clearance` of `public` or `pre-publication`. Nothing about a
specific antibody enters the corpus — CI enforces that mechanically rather than by memory.

## Stage 1 — Sourcing pass and first demo

**Goal.** Every claim in the corpus traces to a source that was read, and Deb and Travis have
seen Abbie work.

**This stage was re-cut because scientist review is not available on the timescale it assumed.**
The original gate required every concept at `status: approved` with `reviewed_by` populated,
which needs an afternoon of a scientist's time that has not been schedulable. Waiting for it
would hold the demo indefinitely, and marking files approved without a reviewer would put a
sign-off in the audit trail that nobody gave. So the corpus now has a third status between the
two: `sourced` means every claim was traced back to a cited public source and checked against
it, which is the highest bar reachable without a scientist. `approved` keeps its meaning and
its `reviewed_by`, and CI fails on an approved file that names no reviewer.

**Deliverables**

- Every concept file at `status: sourced`, each claim checked against the source it cites.
  Review happens as a pull request, so the diff is the audit trail either way.
- The kickoff notes' blank questions split by kind: the ones with published answers researched
  and written, the ones asking IPI to take a position deferred and left visibly absent rather
  than filled in with a plausible number. See corpus/README.md.
- A decision from Deb on 4D publication timing, per the constraint above. Still hers, and still
  the item that determines what the first public release may say.
- Demo, described as running on a sourced corpus rather than an approved one.
- The feedback loop's first turn, run after that demo session. See The feedback loop, specified.
- Langfuse enabled for the demo, which is two environment variables against the exporter
  `packages/telemetry` already builds, so demo traces outlive the session.
- The model-graded judge seam in `packages/eval/checks.py` filled: flag-gated, cached, scored
  against each case's ideal, tracked and blocking nothing. See From answers to workflows.

**Gate.** Corpus at `sourced` with CI green, the deferred questions listed rather than answered,
demo delivered. Scientist sign-off moves to its own gate, taken whenever the time exists.

**Blocked on.** Nothing, which is the point of the re-cut. The 4D publication decision is still
outstanding and still Deb's, but it gates what the *public* surface may say rather than whether
this stage can finish. Scientist sign-off remains wanted, and the ask stays separate from
Stage 3's so the small one is not held up by the large one.

**Estimate.** About two weeks. Sourcing is slower than drafting, because a claim that cannot be
traced has to be rewritten or dropped rather than softened.

## Stage 2 — Catalog identity

**Goal.** Abbie can say which antibodies IPI has, and cite them. No validation claims yet.

**Deliverables**

- Written confirmation that antibodies cleared for Addgene distribution under IPI-CHR-001 are
  the public set, and which fields may be shown. Set membership was confirmed on August 17, 2026;
  the written record of it and the showable-field list are what remain owed. No machine-readable
  release flag exists at the source, so the Addgene-cleared rule is what stands in for one.
- A publication manifest built from that rule: source record ID, release decision, allowed
  fields, approver, timestamp, policy version, public citation URL. Piloted on the 55 design
  variants already carrying RRIDs and Addgene numbers.
- Extract job over the datasheet Airtable — 20 tables, of which the datasheet renderer reads 15 —
  with a column allowlist, fail-closed, writing into Abbie's own Postgres on Cloud SQL. The source
  moved off the Benchling warehouse because that mirror sits on AWS RDS and this project has no AWS
  access; the destination is unchanged. See Stage 4, Open thread.
- `get_antibody` and `search_antibodies` over identity fields only.
- The bounded tool loop those two run inside, implemented on LangGraph as a small `StateGraph` with
  a capped tool-execution loop, and the first workload where the model chooses what to fetch: capped
  calls per turn, the router still deterministic ahead of it so `refuse` and `abstain` never enter
  it, leak scan unchanged. See From answers to workflows, Tool use.
- Web search in log-only mode: record when the model would have searched, and spend nothing. See
  Web search — designed, not scheduled.
- The hybrid retrieval challenger on `pgvector` in the same Cloud SQL instance, as a tracked
  experiment on the standing milestone cadence, shipping into public answers only if it beats the
  full-context baseline on the golden set.
- Leak tests on every publish, plus a change audit.

**Gate.** Confirmed rule, manifest built, leak tests green, no unapproved record reachable
from the application.

**Blocked on.** The written record of the August 17 confirmation and the showable-field list. Set
membership is settled, so what is outstanding is a document rather than a policy exercise.

**Estimate.** Roughly a week and a half once that record exists.

**Scope discipline.** Identity only — target, clone name, RRID, Addgene number, isotype,
species, source URL. Assay evidence is Stage 3.

## Stage 3 — Validation Profiles

**Goal.** Defensible application-specific Validation Profiles for the pilot set.

**Deliverables**

- Mapping from IPI-CHR-001's criteria onto datasheet-Airtable tables: which table and column
  carries each SEC, intact-mass, SPR, Cell Display, polyreactivity, and application-testing result,
  and how each maps onto its dimension. Table1 and the ELISA table already carry clean Pass/Fail
  verdicts, so part of the mapping starts from a graded column rather than a raw measurement.
- Canonical evidence model: one reviewed outcome per antibody, lot, target, application, sample
  type, species, protocol, concentration, version, source.
- Private curation job deriving candidate profiles for scientist review. Only an explicitly
  approved profile crosses into the public database — a derived profile can disclose private
  results even when the underlying rows are withheld.
- Profile rendering in the widget, cited per cell, showing unassessed dimensions as unassessed.
- `get_validation_profile` over the approved profiles, which converts today's abstention on a named
  antibody into a grounded answer inside the pilot set and nowhere outside it.
- The bench checklist promoted from an export endpoint the visitor presses to a tool the model
  invokes inside guided validation planning, so the artifact comes out of the plan it summarizes.
- The runtime critique-and-revise A/B on the golden set, latency budget and detection floor
  pre-registered, adopted only on measured lift. See From answers to workflows, Reflection.

**Gate.** Scientist-reviewed profiles for the pilot antibodies, and the abstention path still
correct outside that set.

**Blocked on.** One thing, and on August 17 it changed shape rather than closing. The original
blocker was that `sec_ab_characterization`, `cell_display_ab_characterization`, and
`psr_ab_characterization` all audited at zero rows while IPI-CHR-001 says those assays run on every
small-scale antibody; the August 7 audit then found the rows in volume under the `$raw` siblings.
That answer is now unusable: the warehouse mirror sits on AWS RDS and this project has no AWS
access, so those tables are out of reach rather than merely unmapped. The open question becomes
which datasheet Airtable tables carry the SEC, Cell Display, and polyreactivity results, and an
Airtable schema census answers it in place of an RDS one.

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
`GROUP BY tier` settle it, and if it is populated, part of Stage 3's mapping already exists. That
check is off the table now that warehouse access is gone, and the observation is kept rather than
deleted because the question it asks is the right one to put to the Airtable schema: whether any
table there already carries a materialized IPI-CHR-001 grading, and what its values are.

**Estimate.** Several weeks, gated more on locating and agreeing evidence than on engineering.

**Design constraint.** No single validation score. See architecture.md, Validation Profile module.

## Stage 4 — Deploy and internal pilot

**Goal.** Abbie runs on IPI-owned infrastructure, used by staff before the public sees it.

**Deliverables**

- Terraform for the full footprint, per [hosting-decision.md](hosting-decision.md): Cloud Run for
  the service, Cloud SQL for the Postgres the extract and the checkpointer share.
- IPI-owned Google Cloud project, IT holding billing, budget alert on from day one.
- GitHub Actions deploy via Workload Identity Federation.
- Staff surfaces: the MCP server and the Slack app over the shared tool library, carrying the
  authoring copilot as a role of its own rather than the public answerer on a different transport.
  See From answers to workflows, Multi-agent orchestration.
- Session persistence, which is deploy-blocking rather than optional: Cloud Run autoscales and
  scales to zero, so the in-process `SESSIONS` dict cannot survive between requests. The engine is
  LangGraph's Postgres checkpointer in the Cloud SQL instance the Terraform stands up, so sessions
  survive a restart and a feedback verdict joins the conversation it was given about. Opt-in
  researcher profiles ride the same store.
- OpenTelemetry tracing and cost monitoring.
- The feedback loop at its weekly cadence, over the signals that tracing makes readable.

**Gate.** Deployed, staff using it, monitoring and budget alerts live.

**Blocked on.** GCP project ownership and budget sign-off.

**Estimate.** Roughly a week and a half.

**Open thread, resolved August 17, 2026.** The kickoff notes carry an action item for Travis on AWS
access. It is moot for Abbie: this project has no AWS access and is not asking for it. The item was
never a competing hosting decision — it was warehouse access, and the Benchling mirror sits on AWS
RDS — so the consequence is a data-plane one. The mirror is out of reach, and Stages 2 and 3 run on
the datasheet Airtable and Addgene instead. Hosting is unchanged and settled: Google Cloud Run, per
[hosting-decision.md](hosting-decision.md).

## Stages 5 to 7 — Third-party coverage, recommendation, public launch

Third-party coverage (RRID, YCharOS, Antibodypedia, CiteAb), experiment-aware recommendation,
then public launch and hardening. Detail in [architecture.md](architecture.md).

**The capability work here.** Stage 5 adds one registry tool per source and the
fan-out that runs them in parallel behind a synthesizer. Stage 6 is the first real
decompose-then-execute plan over that tool layer, built as an extension of the LangGraph graph that
has been carrying the tool loop since Stage 2 rather than as a framework choice made late. See From
answers to workflows.

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

## The feedback loop, specified

The plans name a feedback loop once and never say what it does, which makes it a word rather than a
mechanism. It is a human cadence over signals the system already emits. No dashboard, no annotation
tool, no automated corpus generation — each of those is a thing to build once the cadence has run
long enough to say what it would show, and building one first is how a loop becomes a tool nobody
opens.

**What it reads, and what is actually readable today.** Five signals, four of them readable now:

- **Behavior rates.** On every turn as `abbie.behavior` and `abbie.outcome`. Readable now.
- **Blocked turns.** Already traced as the highest-signal event the system produces: the reply is
  withdrawn from the visitor and kept on the trace, with the question attached, precisely so it can
  be read later. Readable now, and the richest of the five.
- **User feedback verdicts.** Readable as of the `/feedback` endpoint added August 17. The widget's
  thumbs post the verdict and the server puts it on the trace as an `abbie.feedback` span carrying
  the turn index and an up or down score label. Telemetry is the only store, so like every span here
  it needs a configured exporter to outlive the process, which is Stage 4's tracing line and is why
  the pilot-era loop is the one that gets real use out of this signal.
- **Eval per-check trends.** `scripts/eval_trends.py` over the promoted result json. Costs nothing
  to run, which is why it is the signal that will actually get read.
- **Abstain and redirect subjects.** The one gap: partly emitted, not yet readable by this loop. The
  router returns a `subject`, but only on `abstain` — on `redirect` it is set to None — and it goes
  out over the SSE stream to the browser rather than onto the turn span. So the field that says what
  a declined question was *about* reaches the visitor's page and not the trace. Putting `subject` on
  the turn span is a one-attribute change; whether the router should also fill it for `redirect` is
  the real question behind it. Until then this signal is question text under `ABBIE_TRACE_CONTENT`,
  which is off by default for good reason.

**The cadence.** Demo-era, after each demo session. Pilot-era, weekly. Read the abstain and redirect
subjects and the blocked turns from the period, then sort what is there two ways. A question the
corpus could not answer becomes a corpus-concept candidate and a golden-set case — the case first, so
the gap is asserted before it is filled and the fix has something to be measured against. A check
failing repeatedly across runs becomes a prompt change or a budget change, and the trigger table
above is what decides that repeatedly has been reached, so the cadence does not relitigate it every
session.

**Where it attaches.** The demo-era version starts at Stage 1, because the demo audience is the first
set of real users and there is no earlier point at which real questions exist. The pilot-era version
is a Stage 4 deliverable, alongside the monitoring already listed there: the same loop at a longer
cadence over a larger population. By then the one missing piece, `subject` on the turn span, is
either built or the loop runs on four signals instead of five, which is worth knowing in advance
rather than discovering it at the first review.

## Web search — designed, not scheduled

The full design is recorded in [architecture.md](architecture.md), Web search (planned, not yet
built): a server-side search tool on the existing single call (never an agent loop), per-request
search caps and a vetted domain allowlist, search results handled as delimited untrusted data under
the Stage 5 rule, project-scoped API key with a monthly budget cap, per-IP rate limiting and a
kill-switch feature flag shipped first, and a log-only then staff-only then public rollout, each
stage gated on clean spend data and a citation eval partition. Log-only lands at Stage 2 alongside
the first tools, staff-only no earlier than Stage 4 with the internal pilot, and public enablement
no earlier than Stage 7. Nothing beyond the log-only counter is built until the design's rollout
gate is met; the point of writing it down now is that the cost and injection controls are
requirements, not retrofits.

**Evidence check, August 2026.** The restriction had been inherited from the design rather than
tested, so before carrying it further it was researched from both sides.

*For search.* Grounding a model in search results lifts factual-QA accuracy by 32 to 49 points on
FreshQA, the benchmark built out of questions whose answers change over time (Vu et al., ACL
Findings 2024, arxiv.org/abs/2310.03214). The closest deployed analog to the Stage 5 evidence-dossier
workload — BenchSci, mining the antibody literature — is built on search. And a general LLM without
it fabricates biomedical citations rather than declining to produce them, which is the specific
failure the dossier workload cannot tolerate.

*Against, on a public anonymous widget.* Indirect prompt injection through a retrieved page is
operational as of 2025 and 2026, not theoretical: OWASP ranks it first in its LLM Top 10, and even
the best-defended browser agents show roughly 1% attack success under adaptive attack in Anthropic's
own published evaluation. Provider search bills per call, on the order of $10 per thousand, which
makes an authless endpoint a denial-of-wallet target before it is an accuracy question. And embedded
assistant widgets across the industry ship curated knowledge only, not open search.

*The finding that binds the two.* Retrieval measurably erodes abstention — one study puts
appropriate abstention at 84% without retrieval and 52% with it (arxiv.org/pdf/2411.06037). That
attacks the discipline Abbie is built around rather than a peripheral quality metric, so the
abstain-case re-audit already named in the eval gate is an explicit adoption condition rather than a
nicety: search reaches no surface whose abstain cases have not been re-run with it on.

*Verdict.* The staged rollout stands on evidence rather than on inheritance, and the schedule moves
where the evidence said it should. **Log-only mode — record when the model would have searched,
spend nothing — is pulled forward to Stage 2**, alongside the first tools, so demand is measured
years before the public gate rather than guessed at it. Staff-only stays no earlier than Stage 4.
Public stays no earlier than Stage 7, behind the named cost and injection controls.

**What "never an agent loop" bounds, now that there is a tool loop.** It bounds the browsing, not
the turn: no client-side tool-runner and no model-directed iteration on a public endpoint, because
every extra hop out there spends credit and admits untrusted text. It was never a rule against
calling a typed tool against IPI's own database under a per-turn cap. The two coexist — web search
stays one declared server-side tool, with its own caps and allowlist, inside the loop described
under From answers to workflows, Tool use.

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
   (Stage 2). Set membership was confirmed on August 17, 2026, so what is still owed from IPI is the
   written record of that confirmation and the showable-field list.
3. **What "functional" means for SPR, and good versus okay versus bad per application** (Stage 1).
   Narrowed from four questions to this one: monoclonal versus polyclonal and the case for
   recombinant antibodies have published answers and are being researched and written rather than
   asked. This one has no consensus banding to look up, and the framework declines to produce a
   quantitative score by design, so any threshold Abbie states is IPI's position rather than the
   field's. Until it is answered, no concept states a band.
4. **Which name the fourth dimension takes. Settled August 17, 2026: Experimental Readout.** The
   kickoff notes' "Function in Applications" is the superseded older name. Every artifact in the
   repo — the corpus, architecture.md, the golden set, the system prompt — already stood on
   Experimental Readout, so what looked like an open choice was a naming drift in the notes. The
   question stays listed because the older name is still in circulation in the notes.
5. **Whether capability 5 should produce a ranking at all**, given the framework declines to produce
   a single score (Stage 6). See Stages 5 to 7 above.
6. **Whether staff surfaces may expose unpublished data to OpenAI** (Stage 4). Not the account
   question it first looks like. Abbie bills an OpenAI **API** organization, while a ChatGPT MCP
   connector runs inside a **ChatGPT workspace**, a separate tenant with its own terms, retention,
   admin controls, and training defaults. Asked as a question about IPI's existing terms it gets a
   yes for the wrong reason, so it has to be asked about the workspace. The recommended answer makes
   it moot for Stage 4: scope the staff tool surface to the approved extract, so it serves nothing
   the public widget does not. See architecture.md, AI-engineering rationale. Revisit only when a
   reviewed internal dataset exists to serve — there is none today, since only 4 entries in the
   tenant have ever completed review.
7. **Third-party licensing terms and budget** (Stage 5), including whether CiteAb's terms permit a
   ranking, which is a derived work.

Ours to answer, and cheap:

8. **The distribution of `antibody_tier.tier`** (Stage 3). The table is populated — 7,303 rows — but
   the value breakdown is not yet measured. One `GROUP BY` settles whether an IPI-CHR-001 grading
   already exists in materialized form.
9. **Whether the release-gate assay tables join cleanly** to `antibody_lot_registry` and
   `ab_prod_design_variant_registry`, and on which columns (Stage 3).

Both of those were warehouse queries, and both became unaskable on August 17 when AWS access was
ruled out. They are kept because each transfers intact to the source that replaced it: the census
now runs against the datasheet Airtable, asking whether a materialized IPI-CHR-001 grading already
exists there and how its assay tables join to the identity records the catalog extract publishes.

## Resolved by the August 7 warehouse audit

Recorded here rather than deleted, because the earlier answers shaped decisions that are still in
these documents. Measurements are in [warehouse-findings.md](warehouse-findings.md).

- **Where the SEC, Cell Display, and polyreactivity results live.** They exist in volume, under
  different table names than the first audit guessed — `sec_results$raw` (18,792),
  `new_cell_display_results$raw` (16,075), `antibody_psr$raw` (16,854). The `*_ab_characterization`
  tables are empty shells. Stage 3 was no longer blocked on locating this data — until August 17,
  when the loss of AWS access put the rows out of reach and moved the question to the Airtable
  schema. See Stage 3, Blocked on.
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
