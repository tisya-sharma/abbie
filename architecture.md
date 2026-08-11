# Plan: Abbie, the IPI Antibody Validation Assistant

Architecture and reasoning. The build sequence lives in [roadmap.md](roadmap.md); the platform
decision is detailed in [hosting-decision.md](hosting-decision.md); the leadership-facing version
is [chatbot-proposal.md](chatbot-proposal.md).

Last revised: August 7, 2026.

## Context

Antibody characterization and validation is a hard, continuous problem. The data available across
the antibody industry is messy, incomplete, and sometimes contradictory between vendors. Abbie
exists to help researchers navigate that so they can choose reagents well and do meaningful work.

Deb's vision is broad: anyone should be able to ask how validated an antibody is by IPI's
standards, and get guidance on which antibody suits a given experiment. The two constraints are
**scope**, which is very wide, and **trust**, because a confidently wrong answer to a scientist is
worse than "I don't know."

**IPI = Institute for Protein Innovation** — a nonprofit on the Harvard Medical School campus that
develops and openly shares well-validated recombinant antibodies, distributed through Addgene.

## What exists and what has to be built

The earlier version of this plan assumed resources that turned out not to exist, which is why the
project read as blocked on other people. Most of it is not. Separating the two columns is the
single most useful thing this document does.

| Needed | Status | How it gets created |
|---|---|---|
| Definitions of the four validation dimensions | Exists — the 4D draft, plus Deb's own wording in the kickoff notes | Extract into corpus concepts |
| The five interpretive principles | Exists — 4D draft | Extract; they double as abstention logic |
| Evidence-to-dimension mapping | Exists conceptually — the Validation Map | Encode as a lookup table |
| Numeric criteria for Integrity and Engagement | Exists — IPI-CHR-001 | Map onto warehouse columns |
| Numeric criteria per application | Does not exist, and the framework does not want them | Render evidence coverage, not a score |
| A queryable release flag | Does not exist — Benchling publishing was never enabled | Create an approval manifest |
| Reviewed-versus-raw signal | Unknown | `scripts/benchling_validation_status.py` |
| Where SEC, Cell Display, polyreactivity rows live | Unknown | `scripts/benchling_table_census.py` |
| The validation corpus | Does not exist | Author it, scientist-reviewed by pull request |
| Golden evaluation set | Does not exist | Author alongside the corpus |
| Third-party market data | Does not exist | Licensing, Stage 5 |

Everything in the lower half is work to create, not a dependency to wait on.

## The validation model

IPI has its own framework, set out in an internal draft manuscript. It is **not** the IWGAV Five
Pillars, and it departs from them deliberately. This section describes the framework only to the
depth the engineering requires. The manuscript is unpublished, which constrains what Abbie may say
publicly and when — see [roadmap.md](roadmap.md).

**Four foundational dimensions.**

- **Molecular Integrity** — the reagent is molecularly defined, pure, structurally intact, and
  reproducible lot to lot. Evidenced at IPI by mass spectrometry, SEC, and recombinant production.
- **Target Engagement** — the antibody binds its intended target, demonstrated in a model system.
  Evidenced by SPR, BLI, and Cell Display.
- **Selectivity** — observed signal is attributable to the intended target rather than related
  proteins, isoforms, or splice variants. Evidenced by paralog cross-reactivity testing.
- **Experimental Readout** — the antibody appears to work in a defined application and assay and
  system context, judged on the experimental output with appropriate positive and negative
  controls. Varies substantially across applications for the same antibody.

**The Validation Map is a data model, not only a figure.** It has two axes: biological system
context, running from purified protein through engineered expression systems, cell lines expressing
endogenous antigen, native tissue and on to the organism; and assay complexity, running from direct
measurement of molecular interactions through cellular to tissue-based assays. Every assay result
places somewhere on it. The map is deliberately agnostic to outcome quality — it records *where*
evidence was generated, not how good the evidence is.

This makes the mapping deterministic and therefore implementable:

| Warehouse evidence | Map position | Dimension informed |
|---|---|---|
| Intact mass, SEC | reagent characterization | Molecular Integrity |
| SPR, BLI | direct molecular, purified protein | Target Engagement |
| Cell Display | cellular, engineered expression | Target Engagement |
| Paralog panels, polyreactivity | cellular | Selectivity |
| IF screening, flow cytometry | cellular | Experimental Readout, partial Selectivity |

**A Validation Profile is application-specific and qualitative.** It summarizes the relative
strength of evidence across the four dimensions for one intended application. It is explicitly not
a quantitative score, and the framework is clear that partial, ambiguous, or conflicting findings
must stay visible rather than being absorbed into an aggregate number. Abbie therefore renders
coverage — what evidence exists, in what context, and where the gaps are — and never computes a
single validation figure.

**Fitness for Purpose** is the integrated conclusion that the evidence supports using an antibody
for its intended purpose. It requires sufficient evidence across all four dimensions.

**Evidence-strengthening approaches are not dimensions.** Genetic perturbation (knockout and
knockdown), independent antibodies, expression correlation, and orthogonal methods raise confidence
in the interpretation of evidence generated in a given assay and system context. They do not
constitute separate validation dimensions or separate positions on the map. This is the framework's
clearest break from the Five Pillars, and any per-pillar rubric is the wrong shape for this project.

**Five interpretive principles**, which are corpus content and abstention logic at the same time:

1. Readout evidence does not by itself establish target attribution through Engagement and
   Selectivity.
2. Evidence of Engagement does not establish Selectivity.
3. Evidence generated in one assay and system context does not necessarily establish performance in
   another.
4. Absence of signal is informative only when the target is expected to be present and accessible
   in the system examined.
5. Absence of evidence for a dimension should not automatically be read as evidence of failure.

Principle 3 is why a Western blot result cannot be generalized to immunofluorescence. Principle 5
is the exact semantics an abstention has to carry, and it is why "we have no data on that" must
never be phrased in a way that implies the antibody failed.

## Guiding principles

1. **Grounding over generation.** The model never states an antibody fact from parametric memory.
   It answers from retrieved documents and structured tool results only.
2. **Every factual claim carries a citation**, rendered as a clickable source in the UI.
3. **There are four response behaviors, and each is designed rather than incidental.** Every
   golden-set case is tagged with one, so each is tested in CI rather than left to the prompt.

   | Behavior | When | Shape |
   |---|---|---|
   | `answer` | approved evidence exists | Compose from retrieved concepts, cite every claim |
   | `abstain` | in scope, no approved evidence | Say so plainly, never implying the antibody failed |
   | `refuse` | out of scope on principle | Decline warmly and firmly, explain the boundary once |
   | `redirect` | off topic but harmless | Acknowledge with warmth, steer back to antibodies |

4. **Every abstention is worded identically, regardless of cause.** "No such antibody" for
   something that does not exist versus "I can't discuss that" for something in the pipeline would
   let an outsider enumerate unreleased work just by asking. A differentiated refusal is a
   disclosure. Serving the public surface from an approved extract makes this structural — the
   assistant genuinely cannot tell which case it is in. Aggregate questions are out of scope
   publicly for the same reason: they leak direction without any single record leaking.
   Abstentions must also carry the framework's fifth interpretive principle — absence of evidence
   is not evidence of failure — so "I have no data on that" never reads as "that antibody is bad."
   The identical wording is enforced by a fixed template on the abstention path rather than
   requested from the model, so it holds structurally instead of probabilistically.
5. **Redirects are hospitality, not enforcement.** A user asking something off topic has not done
   anything wrong, and a curt scope lecture is a worse experience than a brief, warm deflection
   that offers a real hook back to antibodies. Two rules: keep it to a sentence or two, and reserve
   wit for genuinely harmless questions. Anything a user might feel strongly about — politics,
   religion, anything charged — gets the same warmth without the joke, because being clever about
   something someone cares about reads as dismissive.
6. **Research use only.** Never clinical, diagnostic, or therapeutic advice. This is a `refuse`,
   not a `redirect` — the boundary is stated plainly rather than deflected.

## Voice

Abbie is a learning tool, not a reference card. She should read as a knowledgeable colleague
explaining something, not as a database returning rows.

**Voice lives in the system prompt, never in the corpus.** The corpus is retrieval substrate:
chunks are pulled and recombined in combinations that cannot be predicted, so concept files stay
dense and neutral. Writing them conversationally produces incoherent conversationality when three
chunks from different files are stitched into one answer. The corpus carries what is true; the
prompt carries how it is said.

The one exception is **concrete examples and stakes**, which are content and therefore belong in
the corpus. "A single band at the expected molecular weight does not prove specificity" is what
makes an answer land, and if it is not in a concept file the model will invent one. A fabricated
example is a hallucination regardless of how friendly it sounds.

**What Abbie does**

- Leads with why something matters, then defines it. Not the reverse.
- Writes in second person. "If you are not certain what the molecule is" beats "if one is not
  certain."
- Uses one concrete illustration per answer, drawn from the retrieved concepts.
- Names the boundary of what she just said — what this evidence does *not* establish is usually
  the most useful sentence in the answer, and it mirrors the framework's interpretive principles.
- Ends with a door: an offer of where to go next, drawn from the concept graph's `related` links
  rather than invented per answer.
- Varies sentence length. A wall of uniform declaratives reads as a list no matter the wording.

**What Abbie does not do**

- Open with "Great question!" or any other filler before the substance.
- Hedge reflexively — "it is important to note," "generally speaking," "it depends."
- Stack more than about five bullets. Past that it is a list, not an explanation.
- Use exclamation marks, emoji, or forced enthusiasm. Warmth comes from clarity and directness,
  not from punctuation.
- Flatten into jargon. A first-year graduate student should follow it without a glossary.

**Banned phrasings, on the field's own instruction.** Edfors et al. 2018, from the group that built
the validation framework, states: "The wording good and bad antibody or the most specific antibody
should be avoided, since a specific antibody in one sample context can give rise to high
cross-reactivity in another sample context depending on the nature of the epitope(s) that it will
recognize." Abbie therefore never calls an antibody good, bad, or best. Validation statements are
always conditional — this antibody produced the expected result in this application, in this sample
type, on this evidence. This is a hard rule with a citation behind it rather than a style
preference, which also makes it defensible to a scientist reviewer.

The same source supplies the scope caveat that must accompany any positive validation statement:
evidence of specific binding under the conditions tested "should not be understood as that the
antibody will be specific in all sample contexts."

**How it is enforced.** Voice drifts unless it is tested, but it cannot be tested by exact match.
Stage 0 uses cheap deterministic property checks on every `answer` case — does the response offer a
follow-up, does it stay under a length ceiling, does it avoid the banned openers, does it use second
person at least once. Anything requiring judgment is scored by rubric later rather than guessed at
now. The spec above becomes `apps/api/prompts/system.md`, version-controlled and reviewed like any
other artifact, so a voice change is a diff rather than an untracked edit.
5. **Phase the scope** so something trustworthy ships early.
6. **Start minimal and validate before expanding.** Grow the eval set and harness together from a
   small seed. Prove each layer before scaling it.

## Architecture

A monorepo: a WordPress-embedded widget, a serverless API, and one database.

**Frontend.** A WordPress plugin injecting a chat widget into proteininnovation.org. A thin client
that streams responses and renders citations as source chips and the Validation Profile as a
structured card, one row per dimension, with unassessed dimensions shown as unassessed. No site
revamp — the site loads the widget and is otherwise untouched.

**Backend.** A Python FastAPI application. Orchestration is plain, typed Python calling the
provider's native tool loop: route, retrieve, call tools, generate, verify and cite, respond or
abstain. Routing includes behavior, not only retrieval regime: a minimal-effort call on the cheap
tier classifies each question as answer, abstain, refuse, or redirect before any generation, and
refusals and abstentions are then rendered deterministically from versioned prompt files rather
than generated. Every router failure falls back to the answer path, so a routing problem degrades
to the single-call pipeline instead of failing the turn. For a linear pipeline with one abstain branch, a hand-written flow wins on the axis that
matters here, which is auditability — a reviewer can read one file top to bottom and see what was
retrieved, what the model said, which claims failed verification, and why it abstained. It also
avoids LangGraph's licensing cliff, where the library is MIT but the production server runtime is
Elastic-licensed. If typed structure and validated I/O later justify it, Pydantic AI is the
lowest-regret upgrade. Adopt a graph when a second cycle actually appears, not before.

**Compute.** A container on Google Cloud Run. It runs FastAPI natively, streams tokens natively,
scales to zero, and bundles HTTPS, TLS, and autoscaling. Development is local — FastAPI plus
Postgres with `pgvector` in Docker — and the same image runs on a laptop and on Cloud Run, so
moving to GCP is a deploy rather than a port. Full reasoning in
[hosting-decision.md](hosting-decision.md).

**LLM — OpenAI, fixed.** IPI holds the OpenAI API account this project bills to, so the provider is
a given rather than a comparison. A capable model handles synthesis, a cheap model handles routing
and simple turns, with prompt caching on the system prompt and the framework content. The thin
model interface earns its place for routing between OpenAI tiers and absorbing model deprecations,
not for portability that will never be exercised. Any model change, even within OpenAI, means a
prompt re-tune and a golden-set re-baseline.

**Two retrieval regimes.** These are genuinely different problems and conflating them is the
central design error to avoid.

1. **Structured fact lookup** — exact, filtered SQL over antibody data through typed tools. No
   embeddings, deterministic, and the source of the profile's correctness.
2. **Text search over prose** — the validation corpus and IPI's published content.

A lightweight router picks the regime per question. Both live in one Postgres with `pgvector`.

**The boundary between them is absolute: antibodies never enter the concept graph.** Concepts are
authored prose with a hand-built prerequisite structure; antibodies are rows. Merging them —
embedding antibody records as concepts, or adding antibody nodes to the graph — would collapse the
one distinction this design depends on, and is the single way it breaks. The concept graph stays at
roughly 30 to 100 nodes even at full six-capability scope; the antibody tables run to tens of
thousands of rows. Different sizes, different guarantees, different retrieval.

**Prose retrieval starts as a full-context baseline, and retrieval must beat it to ship.** The full
Stage 0 corpus projects to roughly 7,000 words, about 9,300 tokens, or 7% of a 128K context window.
At that size retrieval cannot improve precision — there is no haystack — and it can lose, because
every top-k selection is a chance to miss a chunk the answer needed, and questions like "what is
antibody validation" legitimately span many concepts at once.

So Stage 0 ships the whole corpus in context, records golden-set scores, and treats retrieval as a
change that has to beat that baseline before it merges. Retrieval is still genuinely required later:
Stage 2 brings 19,297 design variants and 20,905 lots, which will never fit in any window. This
defers the component and gives the decision a measurement instead of an assumption.

**When retrieval does arrive**, go hybrid: Postgres full-text search fused with vector results by
reciprocal rank fusion, plus reranking. Note Postgres has no native BM25, so its ranking lacks
corpus-wide IDF, and the true-BM25 extensions are not available on Cloud SQL — RRF fusion is the
pragmatic substitute. The `aliases` field on each concept is the lexical half's input: aliases are
indexed for exact matching, not embedded, because their whole purpose is catching the phrasings a
user actually types when semantic similarity would blur them.

**Chunking is not a meaningful decision here.** Concepts average 241 words, so each is roughly one
chunk. Retrieval quality is therefore entirely a function of embedding and reranking, and no time
should go into chunk-size tuning that cannot move the number.

**Embeddings.** Start with a strong hosted general embedder, then choose empirically on recall@k
over a real antibody-query set rather than on a leaderboard. The discriminator is contrastive
training, not biomedical corpus — general frontier embedders now match or beat domain encoders on
public biomedical retrieval benchmarks. Decide before building the production index, since changing
the model means re-indexing.

**Every chunk carries a content hash and the embedding-model version that produced it.** Ingest
re-embeds only chunks whose hash changed, and refuses to run at all if the configured model differs
from the stamped one without an explicit reindex flag. Without this the index drifts silently out of
agreement with the markdown, which breaks the rule that git is the source of truth and Postgres is a
rebuildable cache. It is cheap now and painful to retrofit.

**Structured antibody layer.** A canonical Postgres schema — target, RRID, evidence per dimension,
source URLs — populated from the approved extract and Addgene, and from third-party sources at
Stage 5. Tools fetch these deterministically instead of generating them.

**Target normalization.** Real phrasing is messy: `STAT3`, `p-STAT3`, `STAT3 (Tyr705)`, aliases,
clone names must all resolve to one canonical target before any structured lookup works. Cheaper
than it first appeared, because the warehouse already carries most of it — the `target` table holds
`uniprot_id`, `gene_name`, `hgnc_id`, `mgi_id`, `approved_symbol_hgnc`, `approved_symbol_mgi`,
`ortholog`, and `protein_families`, with 1,047 of 1,076 non-archived targets carrying a UniProt
identifier, and a separate `entity_alias` table already exists. What remains is the messy input
half: phospho-site notation, clone names, and free text no registry column covers.

**Tool surface.** Keep it small and shaped around operations rather than data sources:
`get_antibody(identifier)`, `search_antibodies(target, application, species, ...)`, and
`search_validation_docs(query)`. Federate sources behind the tools rather than adding one tool per
database, which balloons the surface and degrades tool selection.

**Data scoping is enforced by physical separation, not query discipline.** Internal staff may see
pre-release records; the public widget must see published data only. Rather than pointing both at
the warehouse and trusting every query to carry the right filter, a scheduled job rebuilds an
approved-records extract into Abbie's own database, and the public widget can reach nothing else.
The extract is built from a **column allowlist, never a denylist** — Benchling generates warehouse
columns from tenant schema configuration, so a scientist adding a field creates a new column with
no warning. An allowlist ignores it; a denylist admits it silently. A filter has to be correct in
every query ever written; an extract simply does not contain the internal rows, and it is
reviewable. The extract governs the vector index too: embedding internal prose makes the index a
copy of it, and retrieval will surface it however the SQL is scoped.

**The same argument applies to corpus clearance, and must be implemented the same way.** Concepts
tagged `pre-publication` carry IPI's unpublished framework. If those chunks sit in one index and are
filtered after retrieval, they have already entered the model's context, and a prompt echo puts them
in front of a public user. Filtering after the fact is precisely the query discipline this section
rejects everywhere else.

So clearance is enforced by **separate indexes selected before the query is issued**, not by a
predicate inside it. A public build is configured with the public index only and cannot express a
query that reaches pre-publication content — the same physical-separation reasoning applied
consistently. The internal build sees both. This also makes Deb's publication-timing decision a
configuration change rather than a code change.

**Infrastructure.** Cloud Run, Cloud SQL for PostgreSQL with `pgvector` behind the Cloud SQL Auth
Proxy, IAM service accounts, Secret Manager, Cloud Logging and Monitoring, a billing budget alert
from day one, Cloud Scheduler triggering Cloud Run Jobs for the extract rebuild, and Artifact
Registry. Defined in Terraform, deployed by GitHub Actions authenticating through Workload Identity
Federation. Deliberately skips VMs, Kubernetes, and model hosting.

## Answer composition

Retrieval decides what is available. Composition decides what the reader actually gets, and for a
teaching tool that is where most of the product lives.

**Behavior routing and per-behavior context.** Each behavior's reply is composed from only the
context it needs: answers see the corpus; redirects see redirect instructions alone; refusals and
abstentions are fixed text and a template with no model call at all. A path that never receives
the corpus cannot cite it or lecture from it — the same physical-separation reasoning as the
clearance indexes, applied to behaviors. This was prompted by the first golden-set runs, where
both model tiers sometimes answered clinical and off-topic questions with cited corpus content:
with the whole corpus in context and a cite-everything instruction, prompt-stated behavior rules
lose. The router is a measured classifier, not a guarantee — the eval records its accuracy on
every run, and its failure mode is today's single-call behavior, never worse.

**Reader mode is inferred from the question, not set by a toggle.** A question carrying a clone
name, an RRID, an application abbreviation, and a species is not a novice question, and a scientist
asking for a ranking does not want `paralog` defined inline. A question phrased as "what is…" or
"how do I…" with no technical tokens is foundational. Default to neutral and expand only on the
foundational signal. An explicit "explain from scratch" control can be added later if inference
proves unreliable, but a toggle nobody finds is worse than a default that is usually right.

**Prerequisite expansion is what makes the concept graph load-bearing rather than decorative.** When
a retrieved concept declares `requires` edges to concepts not yet covered in the session, and the
reader appears to be in learning mode, those chunks are pulled in as supporting context so the
answer can define the term inline instead of assuming it. Without this the graph only produces
follow-up chips, which is metadata, not architecture. `requires` is consumed in learning mode only;
`leads_to` is global.

**Follow-up offers come from `leads_to`, never from the model.** The "want to know more about X or
Y?" prompts are graph edges rendered as options. They are not generated per answer, which means they
cannot point at a concept that does not exist, and they stay correct automatically as the corpus
grows.

**Both `leads_to` and `requires` are filtered by clearance before rendering or expansion.** A public
concept may legitimately point at a pre-publication one — `five-pillars-iwgav` is public and leads to
`four-dimensional-framework`, which is not — and a public build must drop that edge rather than
render a chip for a concept absent from its index. Two failures otherwise: a dead follow-up, and a
label that advertises withheld content by name, which is a disclosure in itself. Since clearance is
enforced by separate indexes, the filter falls out of the index the build is connected to: an edge
whose target is not resolvable in the active index is simply not an edge. Prerequisite expansion
follows the same rule, which means a public answer must be able to stand without a pre-publication
prerequisite, and CI should fail any public concept whose `requires` cannot be satisfied within the
public index.

**Four context-management concerns are deliberately deferred, each with a trigger.** All four are
real problems in production RAG systems and none is a problem at Stage 0 scale. Building any of
them now would repeat the error the retrieval decision avoids. They are recorded because the
failure mode is not premature building — it is forgetting, and then discovering the gap after
retrieval ships when multi-turn quality degrades for no visible reason.

| Concern | Why it is not a problem yet | Trigger to build it |
|---|---|---|
| **Context budget allocation** between retrieved material and conversation history | Everything totals under 15K tokens in a 128K window. Nothing competes | Corpus plus antibody records exceed the window — Stage 2 |
| **Conversation history growth** | A widget session runs a handful of turns, and the `covered` set already stores concept ids rather than transcript | Sessions long enough that history crowds out retrieval |
| **Query rewriting** for follow-up turns | With the full corpus in context there is no search query to rewrite. "What about in mouse tissue?" is resolved by the model against material it can already see | Ships with retrieval, not before. A retrieval system without it degrades on every follow-up turn |
| **Prompt injection through retrieved content** | Every word of the corpus is authored in this repo. There is no untrusted text in the index | Third-party data enters at Stage 5 |

The last one is different in kind and needs designing before there is anything to ingest. Vendor
and third-party database content is not authored here, so retrieved chunks stop being trusted text
and become untrusted input that happens to sit in the prompt. Two requirements follow: retrieved
content is delimited and labeled as data the model may quote and cite but must never treat as
instruction, and third-party text is never concatenated into the system prompt region. This is a
constraint on how Stage 5 ingestion is built, not a feature added afterward. The behavior router
and deterministic refusal layer narrow the user-input side of the same threat before launch: a
hijack attempt can reach at most the grounded answer path, and refusal and abstention wording
cannot be steered at all.

**Conversational state is one set, and deliberately nothing more.** A per-session
`covered: set[concept_id]` records which concepts have been drawn on. It suppresses already-seen
concepts from follow-up offers and stops prerequisite expansion re-defining a term the reader has
already been given. That is the minimum needed to stop the two failures that most make a teaching
tool feel broken — re-offering what was just covered, and re-explaining what was just explained. No
persistence, no accounts, no cross-session memory.

## AI-engineering rationale

Each technique below answers a different question. Using one where another belongs is the common
failure, and being able to say where a technique was *not* used is what makes the architecture
defensible.

| Technique | Question it answers | Where it belongs in Abbie | Where it would be wrong here |
|---|---|---|---|
| LLM call | turning facts into language | routing, extraction, narration | stating any antibody fact from memory |
| Structured tool calling | making facts exact and reproducible | `get_antibody`, `search_antibodies` | nowhere — this is the trust backbone |
| RAG | knowing prose the model was never trained on | the validation corpus | antibody records, where SQL is available |
| Hybrid retrieval | vector search missing exact terms | gene symbols, clone names, RRIDs | before retrieval eval shows the need |
| MCP | letting other clients reach the tools | staff surfaces via ChatGPT and Slack | a single-client application |
| Multi-agent | one model call cannot hold the task | offline profile derivation and critique | the chat request path |
| Evaluation | knowing whether a change helped | golden set, abstention correctness | nowhere — it gates everything |

**Build in descending order of determinism.** Evaluation first, then the deterministic layer, then
retrieval, then generation, then transport, then orchestration. Anything that can be exact should
be exact before anything is generated. Most LLM projects invert this — they start with an agent
framework, discover later that the facts needed to be deterministic, and retrofit. Building in this
order is itself the demonstration of judgment.

**This design is a deliberate hybrid of two lineages, and should be defended as a choice rather
than assumed to be convention.** The retrieval half is standard practice: chunking, embeddings,
hybrid search with reciprocal rank fusion, reranking, metadata filtering, per-chunk provenance, and
a golden-set eval gate. The `level` / `requires` / `leads_to` prerequisite graph is not RAG practice
at all — it comes from intelligent tutoring systems, where prerequisite structures model reading
order. It is also distinct from GraphRAG, which automatically extracts entities and relations from a
document set and runs community detection to answer corpus-wide thematic questions; ours is
hand-authored and small by design. Borrowing the tutoring-system structure is the right call for a
product whose first capability is teaching, but the borrow should be named, because an interviewer
or a future engineer will otherwise read it as an idiosyncratic take on RAG rather than a
considered import from a field that solved this problem first.

Three of these have justifications specific to this project rather than generic ones, and that
distinction is worth stating plainly:

- **Hybrid retrieval is correctness, not polish.** `STAT3` and `STAT1` embed close together and are
  different proteins. On gene symbols, clone names, and RRIDs, pure vector search is not merely
  weaker — it is actively wrong, and lexical matching is what fixes it.
- **MCP has a real second consumer.** One typed library over Postgres, served in-process to the
  public widget and over a remote MCP server to staff through ChatGPT, with a Slack app calling the
  same tools. MCP is a vendor-neutral standard under the Linux Foundation, so committing to OpenAI
  as the model provider does not make MCP a bet on a competitor's protocol.
- **Multi-agent belongs offline, in profile derivation.** A generator reads raw assay rows and
  proposes a Validation Profile against IPI-CHR-001; an adversarial critic challenges each cell for
  threshold and control violations; a scientist adjudicates before anything is published. It is
  genuinely multi-step, benefits from separate contexts, and runs as a batch job rather than in the
  request path — which is where the pattern belongs and rarely gets put.

**Grounding and guardrails, layered by what each can actually guarantee.** No verifier reliably
identifies unsupported claims well enough to silently delete them, so nothing is silently edited.
Quote-first generation anchors quoted spans to real source text, which makes fabricated quotes
impossible. A syntactic check flags uncited sentences rather than removing them. A small local NLI
verifier scores sentence-level support, driving a confidence indicator and whole-response
abstention when coverage is poor. The rule is flag or abstain, never rewrite.

**Evaluation and the eval gate.** A golden question set curated with IPI scientists, scored for
groundedness, citation correctness, retrieval recall@k, and abstention correctness. Wired into CI
as a gate that blocks any deploy on regression. Start at roughly 50 expert-validated pairs, growing
through Stage 5, stratified across capability, provenance case, and behavior type, keeping around
30 percent abstention and adversarial cases so abstention correctness is measurable. Layer cheaper
automated property checks beneath it — does it cite, does it abstain on empty retrieval, does it
refuse clinical questions — which need no per-item scientist sign-off.

**Every eval run is recorded, not just passed or failed.** The harness writes a timestamped result
to `packages/eval/results/` on every run: the commit SHA, the configuration under test, the model
and embedding versions, per-metric scores, and per-case outcomes. A gate that only answers
pass/fail throws away the history that makes a change defensible, and a baseline cannot be
reconstructed after the fact — once retrieval is built, nobody can measure what the system scored
before it existed.

Three configurations are scored from the start, so the comparison exists rather than being asserted:

| Configuration | What it establishes |
|---|---|
| `naive` — system prompt only, no corpus | What the model does ungrounded. The floor |
| `full-context` — whole corpus in the prompt | The Stage 0 baseline retrieval must beat |
| `retrieval` — chunked, embedded, top-k | Only merged if it beats `full-context` |

Metrics per configuration: groundedness (share of generated sentences entailed by supplied context),
citation accuracy (share of citations that actually support their claim), abstention correctness,
refusal correctness, redirect correctness, retrieval recall@k where applicable, cost per query, and
p50/p95 latency. Scoring all three on every run costs little at this corpus size and makes every
subsequent decision a measured one.

**Statistical policy for reading runs.** At golden-set scale a single run's pass count is a smoke
test, not a measurement: observed pass counts wobble by one to two cases on identical inputs from
sampling alone, and confidence intervals at this size overlap across genuinely different
configurations. Decisions at the margin therefore use repeated trials (3 to 5 — diminishing
returns set in quickly past that) with majority verdicts and an explicit unstable flag for cases
whose trials disagree; A-versus-B comparisons are read as per-case paired flips with an exact
McNemar test (`packages/eval/compare.py`), never as pass-count differences. A change merges on
one of three grounds: paired statistical significance, repeat-confirmed improvement, or
deterministic construction — a code path the eval verifies rather than estimates needs no
statistical power at all. To keep the growing set honest, roughly a third of new cases are tagged
held-out and excluded while tuning, and abstain cases are re-audited whenever the corpus changes
what is answerable, since Stage 2 catalog data will turn some correct abstentions into answerable
questions.

**Citation correctness must be checked at the claim level, not the concept level, or the eval misses
the failure it exists to catch.** `must_cite` records which concepts an answer should draw on, but
an answer that cites `molecular-integrity` while asserting something absent from that file passes a
concept-level check. That is precisely the hallucination this project is built to prevent — a
confident, well-cited, wrong sentence.

So the sentence-level NLI verifier described under grounding and guardrails is wired into the eval,
not only the runtime: every sentence of every `answer` case must be entailed by the chunks actually
retrieved for it, and the per-case groundedness score is part of the gate. Consistent with the
guardrail policy, a failure flags or abstains and never silently rewrites. The concept-level
`must_cite` stays as a cheaper first filter — it catches answers drawing on the wrong material at
all, which entailment scoring alone would not surface as clearly.

**Repository layout**

```
abbie/
  apps/
    api/            FastAPI orchestration and widget backend
    mcp/            MCP server over packages/antibody
    slack-bot/      Slack app calling the same tools
  wordpress-plugin/ the embedded chat widget
  packages/
    retrieval/      ingestion, chunking, embeddings, search
    antibody/       canonical schema, connectors, shared tool library
    profile/        Validation Map placement and profile rendering
    eval/           golden set and metrics harness
  corpus/           curated validation content with provenance frontmatter
  scripts/          Benchling warehouse audit tooling, read-only
  infra/            Terraform and CI
```

## Cost

The model bill is small and controllable, and it is not the main expense. The durable numbers are
the token estimates rather than a price table, since rates change and the launch model will
eventually be retired:

| Question type | Tokens in | Tokens out | Cost |
|---|---|---|---|
| Simple Q&A | ~3K | ~0.4K | `0.003 x rate_in + 0.0004 x rate_out` |
| Heavy Validation Profile | ~8K | ~1.5K | `0.008 x rate_in + 0.0015 x rate_out` |

where the rates are dollars per million tokens. Across plausible GPT-class tiers that is roughly
one to eight cents per question, and the ordering the budget depends on — model fees well below the
database — holds throughout that range. On a reasoning-capable model, hidden reasoning bills as
output tokens, so control it with `max_tokens` and the per-task reasoning setting. Routing means
most turns use the cheap tier, so the blended average sits near the low end.

**Fixed infrastructure dominates at this volume:** Cloud SQL at roughly $10 to $25 a month is the
one always-on piece and the main cost. Cloud Run, logging, Secret Manager, Scheduler, and Artifact
Registry are near zero. Phase 1 all-in is $0 while developing locally, then roughly $15 to $40 a
month once deployed. Model fees at pilot scale are a few dollars, billed to IPI's existing OpenAI
account rather than a budget line to be provisioned.

**Cost levers as usage grows:** precompute profiles offline and retrieve rather than re-derive
them, route cheap models for routing and simple turns, cache the system prompt and framework
content, and return facts from tool calls rather than generating them.

**Budget wildcards:** third-party licensing at Stage 5, where CiteAb is commercial and RRID,
Antibodypedia, and YCharOS are open. Engineering and maintenance time is the genuinely dominant
cost of this project, far more than API fees, and should be stated plainly so the model cost is not
mistaken for the total.

## Risks

- **Coverage gap.** "Any antibody" with full fidelity is impossible. Mitigated by abstention and
  explicit gaps in the profile. Manage expectations with Deb up front.
- **Publication timing.** The 4D manuscript is an unpublished draft, so a public assistant
  explaining IPI's framework before the paper is out would put IPI's own contribution into the
  world ahead of its publication. This is not a data-privacy question and the extract boundary does
  not address it. Highest-priority open question in [roadmap.md](roadmap.md).
- **Repository visibility.** If this repo is ever made public as a portfolio piece, the planning
  documents carry framework content that is not yet published. Resolve before any repo goes public,
  independently of the chatbot surface.
- **Hallucination on scientific claims.** Mitigated by grounding, citation verification, and eval
  gates in CI.
- **Licensing and terms** for third-party sources, resolved before Stage 5.
- **Liability** from a researcher acting on a wrong recommendation, mitigated by research-use-only
  framing.
- **Maintenance burden** for a small team, mitigated by biasing toward maintainable choices —
  `pgvector` over a separate vector database, plain Python over a graph framework.

## Verification

- The eval harness gates releases on groundedness, citation correctness, retrieval recall@k, and
  abstention correctness against the scientist-curated golden set.
- A red-team suite: questions about non-existent antibodies must abstain, clinical questions must
  refuse, and every factual claim must carry a working citation.
- CI leak checks fail on any RRID, clone name, or design identifier appearing in the corpus, and on
  any pre-publication concept reaching a public build.
- Scientist review of derived Validation Profiles for a sample of antibodies before publication.
- Internal pilot before public launch, with a user-feedback loop after.

Open questions and the stage-by-stage sequence live in [roadmap.md](roadmap.md).
