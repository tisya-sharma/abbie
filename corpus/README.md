# The Validation Corpus

The educational knowledge Abbie answers from. Every public answer about what antibody
validation is, how it is done, and what IPI requires, is composed from these files.

## What this is, mechanically

Each file is one concept. The files are the source of truth and live in git. An ingest job
splits them into chunks, embeds each chunk, and writes them to Postgres. Abbie retrieves
chunks at query time and composes an answer from them, citing the concepts it used.

You never edit the database. To change what Abbie says, edit a file here and re-run ingest.

## Why concepts rather than question-and-answer pairs

One concept serves many questions. "What is molecular integrity?", "How do I know an
antibody is what it claims to be?", and "Why does IPI run SEC?" all draw on
`molecular-integrity`. Stored as answers, that content would be copied three times and drift
apart. Stored as a concept, it is written once and cited three times.

Real questions also never arrive in the phrasing you anticipated. Retrieval matches against
knowledge, and the model composes an answer for whatever wording actually came in.

## Frontmatter

```yaml
id: molecular-integrity          # kebab-case, matches the filename
title: Molecular Integrity
aliases: [integrity, reagent integrity]   # phrasings a user might use
ask: What is Molecular Integrity?   # the follow-up chip label, phrased as a question a first-time visitor would type
provenance: ipi-authored         # quoted | summarized | ipi-authored | established
sources:                         # required when provenance is summarized
  - label: "Uhlén M, Bandrowski A, Carr S, et al. A proposal for validation of antibodies. Nat Methods. 2016;13(10):823-827."
    url: https://doi.org/10.1038/nmeth.3995
    short: "Uhlén 2016"          # first author and year, how a paper is named out loud
    journal: "Nat Methods"       # standard abbreviation, omit for books
    title: "A proposal for validation of antibodies"
status: draft                    # draft | sourced | approved
reviewed_by:                     # the scientist who approved it, set only at approved
clearance: public                # public | pre-publication
level: core                      # foundational | core | advanced
requires: [what-is-a-reagent]    # prerequisites, always simpler than this concept
leads_to: [assay-sec, assay-mass-spectrometry]   # where to go next, usually deeper
checklist:                       # optional, drives the downloadable checklist export
  - item: Positive control expressing the target at endogenous level
    proves: The assay could have detected the target at all
```

**`checklist`** is optional and only bench-procedure concepts carry it — today
`controls-in-validation` and `application-western-blot`. Each entry is an `item` / `proves`
pair, both required, and the loader rejects an entry missing either.

It is not read by the model. The export at `/export/checklist` composes a fixed template from
these pairs, so the model chooses which concepts apply and never writes the artifact itself,
which is what keeps a downloadable document from becoming something Abbie can improvise. Add
one when a concept describes steps a reader would work through at the bench; leave it off
otherwise.

**`sources`** carries both the full citation and the pieces the widget displays. `label` is the
complete Vancouver-style reference and `url` is what makes a source citable at all; `short`,
`journal` and `title` are what a visitor actually reads, shown as a byline over the paper's title.
Take those three from the resolved record — Crossref for a DOI, PubMed for a PMID, the Bookshelf
entry for a book — rather than by splitting the label string, and leave a field out entirely when
the work genuinely has none. A book has no journal, and inventing one is worse than omitting it.

**How deeply a source must be read depends on what is being claimed of it.** Retrieving the record
is not reading the paper, and reading the abstract is not reading the paper either. Abstracts
disagree with their own full texts often enough to matter: across seventeen studies the median
inconsistency was around a third, and one survey of structured abstracts found numbers in the
abstract that appear nowhere in the article. The risk sits almost entirely in figures rather than
in direction, so the rule splits on that:

- **Full text is required** for any number, denominator, sample size, threshold, stated condition,
  negative result, or limitation. No full text, no number. A figure whose conditions live in the
  methods section cannot be lifted from an abstract, because the abstract is where the conditions
  were dropped.
- **An abstract is enough** for directional and definitional claims, which are then written as what
  the authors report rather than as bare fact.

This is the distinction the evidence ontologies already draw between an experimental finding and an
author statement, and it is worth keeping because it fails safe: the claims an abstract cannot
support are exactly the ones a reader would most want to check.

Closed-access papers are retrieved under institutional licence into `sources/`, which is
gitignored. Europe PMC answers availability, licence and full text in one call and should be tried
first. Do not trust Unpaywall's `is_oa` without dereferencing the URL it gives you: two of this
corpus's own sources report as green open access and resolve to records withdrawn in 2019.

**Unpublished IPI material is never cited.** Deb's notes and the 4D framework draft ground answers,
and their ideas may be used freely, but they carry no `url` and must never appear as a source, on
request or otherwise. `is_publishable()` in `packages/guardrail` enforces this on two independent
conditions, and `leak_scan` blocks any reply whose sources mention them. The ideas are attributed
to IPI in the prose instead, which is what `provenance: ipi-authored` means in practice: the
concept says "IPI views validation as…" and cites nothing.

**When the 4D paper publishes**, replace the `IPI 4D framework, internal draft` label wherever it
appears with the real Vancouver reference plus `url`, `short`, `journal` and `title`, then drop
`internal draft` from `INTERNAL_LABEL_MARKERS` in `packages/guardrail`. Nothing else changes: the
source becomes publishable, the sources block renders it, and the reply cites it like any other
paper. Deb's notes and `IPI-CHR-001` stay internal regardless, which is why no prompt names the
manuscript specifically.

Do not trust a count here. That label sat on nine concepts while the six that *are* the framework,
`four-dimensional-framework`, `antibody-validation` and the four dimensions, carried only Deb's
kickoff notes, so a find-and-replace would have published the paper and never cited it on the
concepts defining it. Silently, and years after anyone remembered. `check_framework_concepts_cite_the_draft`
in `scripts/check_corpus.py` now asserts the property directly, keyed off the prose rather than off
provenance so a new concept explaining the dimensions cannot slip through either. Together with
`internal sources uncitable` and `withheld sources marked`, publication day fails the build in
whichever direction it is done wrong rather than shipping.

**`status`** has three values, and the middle one exists because scientist time is the scarcest
input to this project.

- `draft` — written, not yet checked. Nothing downstream should assume anything about it
- `sourced` — every claim has been traced back to a cited public source and checked against it.
  This is a claim about provenance, not a scientific endorsement, and it is the highest status
  reachable without a scientist
- `approved` — a named scientist has read it and signed off. `reviewed_by` is set only here

Keeping these separate is the point. Collapsing `sourced` into `approved` to unblock a demo
would put a sign-off in the audit trail that nobody gave, and the review diff is the audit
trail. A demo may ship on `sourced` as long as it is described as such.

**`level`** is what stops the corpus recursing forever.

- `foundational` — a visitor with no antibody background can read it cold. **Has no
  `requires`.** This is the floor, and every chain of prerequisites must terminate here
- `core` — the main concepts most questions land on
- `advanced` — depends on core concepts being understood first

**`requires` and `leads_to`** replace a single flat `related` list, because "you need this
first" and "you can go deeper here" are different relationships and behave differently.
`requires` lets Abbie notice a reader needs the simpler concept first. `leads_to` generates the
"want to know more about X or Y?" offers.

`leads_to` usually points deeper, but it is not required to. Fifteen of the current edges point
at an easier concept, and they are right to: after reading what SEC measures, the useful next
step is often back to why reproducibility matters. What `leads_to` means is "a sensible next
question," not "a harder one." `requires` is the edge with a strict direction, because a
prerequisite that is harder than the thing it unlocks explains nothing.

Four invariants govern the graph, all enforced in CI:

1. **The graph must be acyclic.** If A requires B and B requires A, no reading order exists.
2. **A `foundational` concept has no `requires`.** This is what guarantees every chain
   terminates rather than recursing forever.
3. **No `public` concept may `require` a `pre-publication` one.** Prerequisite expansion is
   filtered by clearance, so a public concept depending on withheld content would be
   unexplainable in the build where it actually ships.
4. **Every `public` concept must retain at least one `public` `leads_to` target.** Edges are
   filtered by clearance and by whether the target exists at all, so a concept whose follow-ups
   are all pre-publication or all unwritten becomes a dead end in the public build. This is easy
   to introduce by accident: `antibody-validation` initially pointed at four unwritten concepts
   plus one pre-publication one, leaving the most-asked question in the product with nowhere to
   go.

Edges may point at concepts that do not exist yet — that is how the corpus records its own to-do
list — but rendering resolves against the active index, so an unwritten or filtered target is
simply not offered.

Note that `requires` is *not* constrained to point at a lower level. Level describes reader
difficulty; `requires` describes logical dependency, and two concepts of equal difficulty can
still have an order between them — `four-dimensional-framework` requires `antibody-validation`,
and both are core. Acyclicity is the invariant that matters.

**`requires` is consumed in learning mode only; `leads_to` is global.** A scientist asking to
rank antibodies for IHC in mouse brain does not want `paralog` defined inline, so prerequisite
expansion is scoped to questions that read as foundational. Follow-up offers are useful to
everyone. See [architecture.md](../architecture.md), Answer composition.

**Antibodies never enter this graph.** It models concepts, which are authored prose in the tens
of files. Antibody records are rows in Postgres reached by typed SQL tools, in the tens of
thousands. Merging the two — embedding antibody records as concepts, adding antibody nodes to
the graph — collapses the distinction the whole retrieval design rests on. Nothing else about
this schema matters as much as that boundary holding.

## Files and folders

Folder structure is invisible to the model, but concept ids are not: ids equal filename stems
by construction, and the assembled context carries them in `id` and `follow_ups` attributes, so
the model effectively sees every file name. That is why ids are treated as internal identifiers
— the server scrubs citation markers from user-visible text, and the guardrail leak scan treats
any id that reaches a user surface as a release-blocking failure. Organization for the model is
the frontmatter graph; folders exist only for the humans editing this directory.

The concepts directory is flat today and the loader reads it recursively, so subfolders can be
introduced at any point without touching code. When they arrive, organize by topic
(`dimensions/`, `applications/`, `assays/`), never by classification — a `foundational/` folder
would duplicate what `level:` already records, and two sources of truth drift. Concept ids must
stay globally unique regardless of folder, and each id must still match its filename.

## What earns its own file

Branching is unbounded unless it is governed — "what is selectivity" leads to paralogs, which
leads to isoforms, which leads to splice variants, indefinitely. A concept gets a file only if
it meets at least one test:

1. It is `must_cite` for a golden-set question, so someone will actually ask it
2. It is a `requires` prerequisite of a concept already in the corpus
3. Its term appears in the body of two or more existing concepts, making it load-bearing
   vocabulary

Anything else is a one-sentence gloss inline, not a file. Test 3 is mechanically checkable, so
the rule does not rest on judgment.

**Depth belongs in the answer, not the corpus.** Abbie answers at the level asked. A
foundational term used in an answer becomes an offered follow-up rather than a preemptive
definition, so the corpus can be deep without every answer being long.

## Naming the dimensions

The manuscript establishes each dimension as a full name with a short form: Molecular Integrity
(Integrity), Target Engagement (Engagement), Selectivity, Experimental Readout (Readout).
Abbie follows the same scientific convention — **full name on first mention in an answer, short
form thereafter.** Selectivity has no short form because it is already one word.

They are **dimensions**, never "pillars." Pillars is the IWGAV term for a different framework
that IPI's departs from, and using it collapses the distinction the framework exists to draw.

The five-pillar framework itself is **background knowledge only**: `five-pillars-iwgav` exists
so Abbie can answer a visitor who explicitly asks how IPI's framework relates to it, and for no
other reason. No concept may point a `leads_to` edge at it, no answer may raise it unprompted,
and the eval enforces both (the `no_unprompted_mention` property check). Abbie presents the
four-dimensional framework; the field's framing appears only when the visitor brings it up.

**`provenance`** records where the content came from.

- `quoted` — a verbatim span from a public source, with a URL
- `summarized` — our prose, every claim traceable to a cited public source
- `ipi-authored` — IPI stating its own position. No external citation, because none exists.
  Requires scientist sign-off instead
- `established` — settled textbook knowledge that every reference work states and none owns.
  Also requires scientist sign-off rather than a citation

`established` exists because a real category of content fits nowhere else. "An antibody is a
protein produced by the immune system that binds a specific target" is not IPI's position and
does not trace to a particular paper — it is what every immunology textbook says. Forcing a
citation onto it would mean picking an arbitrary source and implying that claim depends on it.

The category is deliberately narrow, and abuse of it is the obvious risk. Two tests before
using it: could you name three independent reference works that state this without qualification,
and would a domain expert be surprised to see it cited at all? If either answer is no, the
content is `summarized` and needs a real source. `established` concepts may list reference works
under `sources` as further reading, but those are pointers rather than claim-level citations, and
the scientist reviewer is the actual check.

`what-is-a-reagent` was moved out of `established` for exactly that reason: the fit-for-purpose
framing is the field's, traceable to Ayoubi 2025, and both its source labels already described
themselves as claim-level. It is `summarized`.

**A `summarized` concept may still state IPI's position in one place**, and several do —
`antibody-characterization`, `five-pillars-iwgav`, `orthogonal-validation` and
`validation-vs-characterization` each end by locating their subject inside IPI's framework. Give
that sentence an IPI subject ("In IPI's framework…", "at IPI…") and expect no source behind it.
The provenance field records what the file is mostly doing, not a promise that every sentence
traces outward.

Do not promote such a file to `ipi-authored` to resolve the mismatch. That value carries a second
meaning: `cite_resolver` marks IPI-authored concepts *exclusive*, so their citations never merge
with a neighbor's. That is right for a file whose whole content is IPI's position, and wrong for
one whose externally sourced majority should combine normally.

**`clearance`** controls what may reach a public build.

- `public` — may ship
- `pre-publication` — built and usable internally, blocked from public builds by CI

**The rule that actually binds is about verbatim text, not ideas.** Deb supplied the 4D
manuscript specifically so the framework would guide Abbie's answers, so the framework is
`public` and shapes the corpus as intended. What must never appear is manuscript wording copied
across before the paper is published. Every 4D concept here is written in our own prose from the
framework's structure, which is the distinction that matters.

`pre-publication` therefore currently tags nothing. It is retained because the switch costs
nothing and gives IPI an option if any future content needs holding back — and because the
separate-index machinery behind it is the same mechanism that will scope internal-only antibody
data later.

## How a concept teaches

The system prompt owns Abbie's register — warmth, second person, the follow-up offer. The
corpus owns pedagogical structure: the order ideas arrive in, the concrete anchors, and the
analogies. The split matters because the model can rephrase what it is given but must never
invent an image or example, so any analogy Abbie uses has to be authored and approved here.

Foundational and core concepts follow a teaching shape:

1. **Open with something the reader can picture** — an image, a scenario, a contrast — before
   the term being defined. "Picture a protein shaped like the letter Y" beats "an antibody is
   a protein that" because the reader has somewhere to put the details that follow. The test
   when reviewing a draft: after paragraph one, what does a reader see in their head? If the
   answer is nothing, the opener is abstract and should be rebuilt.
2. **Introduce each technical term at its point of need**, with a plain gloss in the same
   sentence. Never front-load vocabulary.
3. **One idea per paragraph**, and the paragraph's first sentence carries it.
4. **Close by naming the boundary** — what this concept does not tell you. That sentence is
   usually the bridge to the `leads_to` targets, and it is often the most useful line in the
   file.

Analogies are content and get reviewed like claims: an analogy that misleads is worse than no
analogy. Prefer ones that stay true under scrutiny — a hand gripping one patch of a ball
survives being pushed on; a lock and key implies a perfection that the whole corpus exists to
qualify.

Two boundaries on this section, so it ages well:

**It is review guidance, never CI.** The graph invariants are machine-enforced because a
violation is always a bug. The teaching shape requires judgment — a definition-first opener is
usually weaker, and "usually" is a human word. Turning this into a lint rule would produce
ritual openers written to pass the check. If a future maintainer is tempted to mechanize it,
the correct move is to say no.

**It governs explanation-type concepts.** Everything here today teaches, so the shape fits
everything. Later content — assay parameters, per-application reference detail — may be
legitimately reference-shaped, where a reader arrives needing a fact rather than an
understanding. Do not contort reference content into a teaching arc; state which kind a file
is and shape it accordingly.

## Rules

1. **No antibody-specific content.** No RRIDs, clone names, design identifiers, or claims
   about individual antibodies. This corpus is methodology only. CI fails the build on any
   identifier pattern.
2. **Every factual claim in a `summarized` concept traces to a source that was actually
   retrieved and read.** A fabricated citation is worse than no answer.
3. **Self-contained prose.** No "as discussed above" or "this document" — a chunk may be
   retrieved alone.
4. **One concept per file**, so a scientist can review one in two minutes as a pull request
   diff. The diff is the audit trail.

## The concept map

Thirty-two concepts written, and no `leads_to` edge points at an unwritten file, so every
follow-up the widget can offer resolves. That is a property of the corpus as it stands rather
than one CI enforces: the loader fails a concept only when *none* of its follow-ups resolve, so
a typo in one id on a concept with several is filtered out silently at render time. This map
reflects the August 7 sourcing pass, three
concepts added on August 12 to close the bench-controls gap described below, thirteen added on
August 13 covering the framework and the assays, `species-cross-reactivity` added on
August 15, and the per-application concepts written from August 16.

One file, `application-immunofluorescence`, is at `status: sourced`: every claim in it was
traced to a source that was retrieved and read as the file was written. All three of its sources
are closed access and were read at abstract depth, so under the depth rule below it states no
figures at all. The numbers those papers report are held back until the full texts confirm them.
The rest of the corpus is still at `status: draft`. No file names a reviewer, so the grounding
column below records what a concept was written from rather than a claim that a scientist has
checked it.

### Written

| id | level | clearance | grounding |
|---|---|---|---|
| `what-is-a-target` | foundational | public | Kumar 2023, Janeway, Van Regenmortel |
| `reagent-reproducibility` | foundational | public | Bradbury 2018/2015, Ayoubi 2023/2025, Uhlen 2016, Freedman 2015 |
| `antibody-validation` | core | public | Deb, kickoff notes |
| `what-is-binding` | core | public | Uhlen 2016, Janeway glossary |
| `species-cross-reactivity` | core | public | Pruvost 2023, Hu 2025 |
| `paralogs-and-isoforms` | core | public | Uhlen 2016 |
| `five-pillars-iwgav` | core | public | Uhlen 2016, Ayoubi 2025 |
| `application-specificity` | core | public | Uhlen 2016, Taussig 2018, Biddle 2024, Ayoubi 2025 |
| `four-dimensional-framework` | core | public | 4D draft, kickoff notes |
| `molecular-integrity` | core | public | Deb, kickoff notes |
| `target-engagement` | core | public | Deb, kickoff notes |
| `selectivity` | core | public | Deb, kickoff notes |
| `what-is-an-antibody` | foundational | public | established, reference works |
| `what-is-a-reagent` | foundational | public | Ayoubi 2025, Uhlen 2016 |
| `genetic-perturbation-controls` | advanced | public | Uhlen 2016, Ayoubi 2023/2025, Smits |
| `experimental-readout` | core | public | 4D draft, kickoff notes |
| `controls-in-validation` | core | public | Pillai-Kastoori 2020, Ayoubi 2023/2025 |
| `application-western-blot` | core | public | Pillai-Kastoori 2020, Ghosh 2014, Tsuji 2020 |
| `why-validation-matters` | foundational | public | Uhlen 2016, Taussig 2018, Biddle 2024, Baker 2016, Bordeaux 2010, Polakiewicz 2015 |
| `antibody-characterization` | core | public | Ayoubi 2025, Uhlen 2016, Kahn 2024, 4D draft |
| `validation-vs-characterization` | core | public | Ayoubi 2025, Taussig 2018, 4D draft |
| `validation-map` | core | public | 4D draft |
| `validation-profile` | core | public | 4D draft |
| `fitness-for-purpose` | core | public | 4D draft |
| `interpretive-principles` | core | public | 4D draft |
| `evidence-strengthening-approaches` | core | public | 4D draft |
| `orthogonal-validation` | advanced | public | Uhlen 2016, Ayoubi 2025, Edfors 2018, 4D draft |
| `assay-sec` | advanced | public | IPI QC standard, internal |
| `assay-mass-spectrometry` | advanced | public | IPI QC standard, internal |
| `assay-spr-bli` | advanced | public | IPI QC standard, internal |
| `assay-cell-display` | advanced | public | IPI QC standard, internal |
| `application-immunofluorescence` | core | public | Stadler 2010, Schnell 2012, Stadler 2013 |

The four assay concepts carry no numeric criteria. The bands live in IPI's internal release-gate
standard, and what "good" means per application is recorded below as deferred pending a
scientist. Describing what an assay establishes needs no threshold.

What they do carry, in one case, is a qualitative disposition: `assay-cell-display` states that
polyreactive signal against the controls takes an antibody out of consideration. That is IPI
describing its own process rather than a performance grade, which is the line that matters here.

### Still to write

The four remaining per-application concepts: immunohistochemistry, flow cytometry, ELISA, and
immunoprecipitation. These are the open half of the sourcing gap below —
`application-western-blot` closed the Western blot entry on August 12 and
`application-immunofluorescence` closed immunofluorescence on August 16, and between them they
are the template for the rest. None is a dangling `leads_to` target, so the graph is complete
without them; they are coverage rather than repair.

Each remaining one gets its golden-set question written before its prose. The corpus and the
golden set are otherwise authored together, a concept earning its file by being `must_cite` for
a case that the same person wrote alongside it, and inverting the order is what stops a concept
from setting the test that certifies it.

`recombinant-vs-conventional` was dropped rather than written. `reagent-reproducibility` already
covers monoclonal, polyclonal, and recombinant with verified figures, down to its aliases, so a
separate file would have duplicated it.

## Known sourcing gaps

Recorded rather than papered over. Each blocks a concept, and none should be written from
background knowledge — an unsourced claim in a scientific corpus is the exact failure this
project exists to prevent.

Resolved since first recorded: `what-is-an-antibody` and `what-is-a-reagent` are now written
under the `established` provenance, which exists for settled knowledge no single source owns.
They carry reference-work pointers rather than claim-level citations, and their check is
scientist sign-off — flag them for particular attention in review.

**Avidity closed on August 15.** The definition was retrieved from the Immunobiology glossary,
which distinguishes affinity as binding at a single site from avidity as the sum of binding at
multiple sites, and `what-is-binding` now carries it. This was worth closing rather than
deferring because `assay-sec` already used "apparent avidity" as a term of art, so the corpus
was leaning on a word it never defined.

| Gap | Effect | What would close it |
|---|---|---|
| **Isoform and splice-variant attribution** — only paralogs are sourced | Stated as an explicit limit inside `paralogs-and-isoforms` | Unknown whether published guidance exists |
| **What each application measures** — beyond the conformation and sample-preparation axis | Closed for Western blot on August 12 and immunofluorescence on August 16; still open for the other four | Per-application methods literature. Pillai-Kastoori 2020, Ghosh 2014 and Tsuji 2020 closed it for blotting; Stadler 2010, Schnell 2012 and Stadler 2013 closed it for immunofluorescence. Equivalents are what the remaining four need |
| **Mechanism of lot-to-lot variation** — beyond "finite resource" and "genetic drift" | `reagent-reproducibility` stops at those two mechanisms | Not yet identified |
| **Communicating validation to non-experts** | No published guidance found; Abbie's approach is adapted from scientist-to-scientist reporting principles by analogy, which should be stated rather than implied | Science communication literature, or portal documentation |

## Claims that must never enter this corpus

Refuted during adversarial verification on August 7. Several are widely repeated, so they will
resurface — this list exists so they can be rejected on sight rather than re-litigated.

- **"More than half of commercial antibodies failed in at least one application."** The most
  quotable line in this field, and not supported by the paper it is attributed to.
- **The Human Protein Atlas figure** of roughly 55,000 polyclonal and 5,000 monoclonal antibodies
  with about half performing satisfactorily.
- **The clean two-class taxonomy of linear versus conformational epitopes.** Discontinuous
  epitopes may be described, but not as a settled binary.
- **That extra hybridoma antibody chains measurably degrade specificity and signal.** The 31.9%
  figure stands; the performance consequence does not.
- **That the five pillars each work without prior knowledge of the target.**

## Two questions left blank in the kickoff notes

They are not the same kind of question, and treating them the same is what kept both stuck.
One is now answered; the other is still deferred.

1. **What "functional" means for SPR, and what good versus acceptable versus poor looks like
   per application.** Deferred, not researchable. The literature has no consensus banding to
   look up, and the 4D framework declines to produce a quantitative score by design, so any
   thresholds Abbie states would be IPI's position rather than the field's. This waits for a
   scientist. Until then no concept grades antibody performance, and questions that ask for a
   band are answered qualitatively or abstained on. This is narrower than "no concept states a
   number": `controls-in-validation` says a knockdown is generally expected to remove at least
   half the target protein, and reports the expression range one program screened its cell lines
   for. Those describe whether a control is fit to interpret, which is a methodological
   requirement rather than a verdict on a reagent.
2. **Monoclonal versus polyclonal, and why recombinant antibodies are preferable.** Answered,
   and not in a file of its own. It was resolvable from published sources, and
   `reagent-reproducibility` now carries it: all three formats, the head-to-head Western blot
   figures, and the authors' own caveat that the advantage is correlational. It also holds the
   alias a visitor would ask under. This is why `recombinant-vs-conventional` was dropped rather
   than written, as recorded under Still to write above.

The distinction generalizes: a question with a published answer gets researched and written at
`sourced`. A question that asks IPI to take a position gets deferred and stays visibly absent
rather than being quietly filled in with a plausible number.
