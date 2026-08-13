# Abbie

A grounded antibody-validation assistant for the Institute for Protein Innovation.

Abbie answers what antibody validation and characterization mean, how an antibody should be
validated, and — as approved data becomes available — how well characterized a given antibody
is. Every factual claim carries a citation, and the assistant abstains rather than guesses.

Status: Stage 0 near its gate — 30 concepts with every follow-up edge resolving, behavior
routing, per-behavior composition, the output guardrail, the streamed web demo, and a 41-case
golden set are all working, and the corpus and unit checks run in CI. What remains for the gate
is an eval run against the current golden set. The five per-application concepts beyond Western
blot are the open coverage gap, and the corpus is at `status: draft` pending a sourcing pass.

## The documents, and who each is for

| Document | Audience | Purpose |
|---|---|---|
| [roadmap.md](roadmap.md) | me | The operational sequence — stages, deliverables, gates, blockers. **Start here.** |
| [architecture.md](architecture.md) | me, and any future engineer | Architecture, technology choices, and the reasoning behind them. The source of truth for design and cost. |
| [chatbot-proposal.md](chatbot-proposal.md) | Deb and leadership | The proposal and the asks. Non-technical. |
| [hosting-decision.md](hosting-decision.md) | IT | Why Abbie needs its own environment and what the Google Cloud footprint is. |
| [warehouse-findings.md](warehouse-findings.md) | the science team, and me | What the Benchling warehouse actually contains, recorded as measurements rather than conclusions. |

Where these overlap, precedence runs: **roadmap.md** for sequence, **architecture.md** for design
and cost, **warehouse-findings.md** for what the data actually is. The proposal and hosting
documents restate conclusions for their audiences and should be updated to follow rather than
lead.

## The short version

Abbie is built on **IPI's own 4D framework** — Molecular Integrity, Target Engagement,
Selectivity, Experimental Readout — with evidence reported as an application-specific
Validation Profile. This is deliberately not the field's Five Pillars; the framework departs
from them, and an earlier version of this plan had it wrong.

The warehouse audit shaped the sequence. IPI's antibodies are well characterized and the
supporting evidence is there in volume — every assay IPI-CHR-001 treats as universal has tens of
thousands of rows behind it. What the warehouse does not have is a machine-readable flag saying
which records are public, and it never will: Benchling's publishing feature was never enabled and
its review pipeline is not part of IPI's workflow. So the approval manifest is the review gate
rather than a workaround for one. The criteria themselves already exist — IPI-CHR-001 defines what
an antibody must pass before Addgene distribution — so what IPI supplies is a confirmation and a
mapping, not a policy written from scratch.

Abbie therefore leads with the validation corpus: what validation is and how to do it, grounded
in IPI's framework and cited throughout. It needs no data decisions, it is useful on its own,
and it is where every abstention about an unknown antibody has to land.

One constraint to know before reading further: the 4D framework is an **unpublished draft
manuscript**, so what the public surface may say about it is an open question with Deb. See
[roadmap.md](roadmap.md).

## Repository layout

```
corpus/         the concept corpus — see corpus/README.md
packages/
  corpus_loader/  load, validate, and assemble the corpus for a build target
  router/         one cheap call classifying behavior, subject, and question form
  composer/       per-behavior composition, with context separated by behavior
  guardrail/      output-side scrub, leak scan, and the publishability rule
  export/         the downloadable checklist, composed from reviewed frontmatter
  eval/           golden evaluation set, scorer, and paired-run comparison
apps/
  api/            FastAPI server, prompts, and the widget it serves
  cli/            interactive full-context baseline
scripts/        corpus gate checks, and Benchling warehouse audit tooling
schema-audit/   audit output, gitignored
config/         local connection configuration, gitignored
```

The rest of the application layout is specified in [architecture.md](architecture.md), which also
records the approved-but-unbuilt web search design (server-side tool, hard cost caps, staged
rollout) under "Web search (planned, not yet built)".

## Running the baseline

Stage 0 runs the whole corpus in context — no database, no embeddings, no retrieval. The only
requirement is an OpenAI key. Paste it into `.env` at the repo root (copy `.env.example` if it
does not exist) — the file is gitignored and read automatically on startup, and an exported
`OPENAI_API_KEY` always wins over it. The key never goes in a tracked file.

```bash
python3 apps/cli/chat.py
```

By default each question is first routed to one of the four behaviors by a cheap classifier
call; refusals and abstentions are then served from fixed templates with no model call, and
redirects run without the corpus in context so they cannot lecture from it. `--baseline` skips
routing and runs the original single-call full-context pipeline. `--ask "question"` answers
once and exits, `--internal` includes pre-publication concepts, and `ABBIE_MODEL` overrides
the default model. The loader validates the graph invariants on startup and refuses to serve
a corpus that fails them.

## Running the demo

The same pipeline over HTTP, with the widget mounted into a mock site backdrop so the
corner framing is visible while developing.

```bash
uvicorn apps.api.main:app --reload --port 8811
```

Then open http://127.0.0.1:8811. Port 8811 rather than uvicorn's default 8000, which collides
with an unrelated local service. Both endpoints refuse cross-origin requests outright, so a
foreign page cannot spend the OpenAI key against a localhost port. There is no persistence and
no accounts: session state lives in the process and goes away with it.

## Checks

Everything here runs without an API key, and runs in CI on every push.

```bash
find packages apps -name 'test_*.py' | sed 's|/|.|g; s|\.py$||' | xargs python3 -m unittest
python3 scripts/check_corpus.py
```

The corpus gate covers the graph invariants, the clearance vocabulary, the review status and
its sign-off, the antibody-identifier rule, and the rule that an internal source may never
carry a url. The eval is not in CI, because it spends OpenAI credit on every push:

```bash
python3 packages/eval/run.py --dry-run --configs routed --include-holdout   # cost projection
python3 packages/eval/run.py --configs routed --repeats 3 --include-holdout # the gate run
```

## Warehouse audit tooling

The scripts in `scripts/` connect to the Benchling warehouse read-only and inspect structure
and aggregate counts, never record values. They require a `config/benchling.local.json` and a
password in the macOS Keychain, neither of which is in version control.

```bash
python scripts/configure_benchling_connection.py
python scripts/benchling_schema_audit.py
python scripts/benchling_aggregate_readiness.py
python scripts/benchling_table_census.py
python scripts/benchling_validation_status.py
```

Run the schema audit first — the census and status scripts build their queries from its output,
so they only ever reference columns known to exist. The aggregate readiness script covers a
hand-picked 14 tables and is superseded for coverage purposes by the census, which counts all of
them.

These are an offline audit tool. The application will never hold Benchling credentials or a
network path to the warehouse — it reads only an approved extract in its own database.
