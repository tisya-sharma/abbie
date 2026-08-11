# Proposal: An Antibody Validation Chatbot for the IPI Website

Tisya Sharma

## Overview

I'd like to build a chatbot for the IPI website that lets a researcher ask how
well-validated or characterized an antibody is by IPI's standards, and get guidance on
which antibody to use for a given experiment. The idea is ambitious on purpose: it would
take the rigor IPI already applies to its own antibodies and make it directly useful to
anyone trying to choose a reagent. That fits squarely with what IPI exists to do — develop
well-validated antibodies and share validation data openly.

This proposal lays out what the tool would do, where the genuinely hard parts are, how I'd
approach building it, what it would cost to run, and what I'd need from IPI to make it
happen. I plan to work on it five days a week, around five hours a day.

## What it would do

When a researcher asks about a specific antibody, the assistant would return a clear
picture of the validation evidence that actually exists for it: which applications it has
been tested in — Western blot, IHC, immunofluorescence, flow cytometry, ELISA,
immunoprecipitation — and which validation criteria it satisfies, with every claim linked
back to its source. Where the evidence is thin or missing, it would say so plainly instead
of filling the gap with a guess.

It would also help with selection. Given a target, an application, and a species, it would
propose candidate antibodies and explain the reasoning behind each suggestion, again with
citations the researcher can follow.

## Being honest about what's hard

Two parts of this are genuinely difficult, and I'd rather name them up front than
oversell the tool.

The first is the phrase "any antibody on the market." IPI has characterized its own
collection thoroughly, but for the wider market, validation evidence is spread across
external databases with uneven coverage. No single source describes how validated every
antibody is. The assistant handles this by reporting what it can find, citing it, and
abstaining where there is nothing to cite — it will not invent an assessment for an
antibody nobody has characterized. That honesty is what makes it trustworthy rather than
just impressive.

The second is that, for a scientific audience, a confidently wrong answer is worse than no
answer at all. So the system is built so that the model never states antibody facts from
its own memory. It only summarizes retrieved records and database query results, and it
cites everything it reports. Trustworthiness here is a property of how the system is built,
not a disclaimer added at the end.

## How I'd build it

I'd build it in stages, each one producing something concrete and usable before moving on.

**The methodology assistant.** The first working version answers what antibody validation
and characterization actually are, and how an antibody should be validated — grounded in
IPI's own published standards and the field's established criteria, fully cited. It abstains
on every question about a specific antibody.

**IPI's catalog.** Abbie can name which antibodies IPI has and point to them, working from
a list of records IPI has explicitly approved for public release.

**Validation Profiles.** Abbie reports what validation evidence exists for each approved
antibody, organized by our four dimensions and by the assay and biological system the evidence
came from, with gaps shown as gaps rather than absorbed into a summary judgment.

**The broader market.** Connect the external antibody databases and extend profiles to
third-party antibodies.

**Experiment-guided recommendations.** Take a researcher's experiment details and turn
them into ranked antibody suggestions.

**Public launch.** Harden it, put it on the website, and add monitoring and a feedback
loop.

Leading with the methodology assistant is a deliberate choice, and it changed after I audited
our warehouse. It is genuinely useful on its own — "how do I validate an antibody" is a
question we field constantly — and it needs no data decisions from anyone, so it can be built
and shown while the questions below are still being answered. It is also where every "I don't
have validated data on that" answer needs to land: the honest response to an unknown antibody
is to explain what validating it would take. That has to exist before the antibody stages are
worth much, so it comes first regardless.

As for where Abbie would live: she'd appear as a chat bubble in the corner of the existing
website, added through a small WordPress plugin, so the site itself wouldn't need to be
touched. The engine behind the chat — the part I'm actually building — has to run somewhere
separate. Our website's hosting serves web pages; it can't run a custom application with a
database and AI behind it. So having a separate home for the application isn't really a
choice — something has to host it, no matter how we build it.

Where that home should be is the real choice, and we've settled on **Google Cloud**. Abbie
runs there as a container on Cloud Run, with a managed Postgres database alongside it. That
setup suits us well: it costs nothing when nobody is asking it questions, it handles
streaming replies so answers appear as they're written rather than after a long pause, and
the whole thing is defined in configuration files rather than clicked together by hand — so
it's reproducible and can be handed to a future developer rather than living only with me.
The application itself is a standard container, so it isn't locked to Google; the same
software would run elsewhere if we ever needed to move it.

I'd keep the rollout low-risk by building locally first. Everything runs on my own machine
while I develop, which costs nothing and needs no setup on IPI's side. Because the
application is packaged as a container, moving it to Google Cloud later is a deployment step
rather than a rebuild. We'd only stand up an official IPI project — with IT owning it and the
billing — once there's something working and we're ready to put it on the real site. The data side does need care, though. IPI's antibody records live in our Benchling warehouse.
Benchling scopes each credential to the projects that user can read, so it isn't wide open — but
within those projects it returns everything: unpublished work, draft results, archived records,
and a user table carrying staff names and email addresses. So rather than pointing the assistant
at the warehouse directly, I'd build an explicit extract: a job that copies only approved
records, through an allowlist of columns, into Abbie's own small database — the only thing the
public assistant can read. That way what's publishable is a table someone can review and sign
off on, rather than a promise about how carefully every query was written.

## Whether the data exists to do this

Because the feasibility of the whole idea rests on what data we can actually query, it's
worth being precise. The honest answer is that no single database grades every antibody —
the evidence is partial and spread across several sources:

| Source | What it provides | Access |
|---|---|---|
| IPI Benchling warehouse and Addgene | IPI's own well-characterized collection — the highest-quality data available to us, though it needs curation before publication (see below) | Internal / partner |
| Antibody Registry (RRID) | 2.5M+ antibodies with unique IDs; the backbone for matching antibodies across sources | Open |
| YCharOS | Open, knockout-based characterization of commercial antibodies; the best "how validated" data, with limited but growing coverage | Open |
| Antibodypedia | Open application-performance data | Open |
| CiteAb | Citation-ranked antibodies, with links to published images and YCharOS data | Commercial license |

This is exactly why the tool cites what it finds and abstains on gaps. Broadening to the wider
market depends on the sources above, and in particular on a CiteAb license.

I should be equally precise about our own data, because I audited the warehouse in full — all 513
tables — and it changed my picture twice. My first pass checked a handful of tables by name, found
several empty, and concluded the supporting evidence was thin. That was wrong: I had guessed the
wrong table names. Counting every table shows the evidence is there in volume. SEC has 18,792 rows,
SPR 55,526, polyreactivity 16,854, Cell Display 16,075, titer 16,953. Every assay IPI-CHR-001
treats as universal has real data behind it, and immunofluorescence and flow cytometry carry
substantial application-level evidence as well.

What the warehouse genuinely lacks is a way to say which records are public. Benchling's publishing
feature has never been switched on, and its notebook review pipeline is not part of how we work —
four entries in the entire tenant have ever completed review. So there is no release flag to read,
and none is coming. That sounds worse than it is: IPI-CHR-001 already defines what an antibody must
pass before we distribute it through Addgene, so our release criteria are written down even though
they aren't queryable. What I need is a confirmation that the Addgene-cleared antibodies are the
public set — not a publication policy invented from scratch. The approval list we create is the
review gate, and it was always going to have to be. The full measurements are in
`warehouse-findings.md`.

IPI's standard itself is already defined, and by us rather than by the field. The 4D framework
sets out four foundational dimensions — Molecular Integrity, Target Engagement, Selectivity, and
Experimental Readout — together with a Validation Map that records the assay and biological system
each piece of evidence came from, and application-specific Validation Profiles built on top. It
departs deliberately from the field's Five Pillars, treating knockout, independent antibodies, and
expression correlation as approaches that strengthen interpretation rather than as dimensions in
their own right.

That matters for what I have to build. The framework is intentionally qualitative and does not
propose a scoring system — it holds that partial or conflicting findings should stay visible rather
than be concealed within an aggregate number. So Abbie renders evidence coverage per dimension and
never computes a single validation score, which is both what the framework asks for and the more
honest output. What remains is engineering: mapping our warehouse assays onto the dimensions they
inform.

## What I'd need from IPI

To build and run a first version, I'd need support in a few areas.

**Funding for the infrastructure.** The running cost is genuinely small. While I'm building,
everything runs on my own machine, so it costs nothing at all. Once we deploy to Google
Cloud, the bill is mostly the database — the rest of the hosting is near zero at our volume,
and the questions themselves come to a few dollars a month.

| Item | Monthly cost |
|---|---|
| OpenAI API — development, testing, and pilot questions | ~$5-$25, on IPI's existing OpenAI account rather than new spend to provision |
| Database (managed Postgres on Google Cloud) | ~$10-$25 |
| Backend hosting (Cloud Run, pay per request) | ~$0-$5 |
| Embeddings | ~$5 one-time, negligible after |
| Logging and monitoring | Free tier |
| **Total** | **$0 while developing locally, then ~$15-$40 / month once deployed** |

To be safe I'd ask for an operating budget with a ceiling of around $50 a month — above what
I expect to actually spend — with a billing alert so there are no surprises.

**A CiteAb license, for the market-wide phase.** CiteAb's data sits behind a commercial
API license; the other external sources are open. I don't have a price yet, so I'd ask for
the go-ahead to request a quote and for in-principle willingness to fund it when we reach
that phase. It isn't needed to get started.

**Access to IPI's data.** I already have read access to the Benchling warehouse, and I've
audited what's in it. What I need is a list of records approved for public release. I had
expected to find this in the warehouse as a status I could filter on, but Benchling's
publishing feature has never been enabled here, so no such flag exists — which means the
approval list is something we have to create rather than something I can query. I'd suggest
starting small: 10 to 20 antibodies that are already public through Addgene, with the exact
fields that may be shown. That is enough to build and test the entire publication pipeline,
and it can grow once the pattern is proven. I'd also need access to the Addgene collection
data and permission to ingest the public website content.

**A small amount of science-team time, soon.** For the methodology assistant I'd draft short
explainers on validation and characterization and ask a scientist to correct and sign off on
them. This is on the order of an afternoon, and it's the only science input the first stage
needs.

**More science-team time, later — but less than I first expected.** I had assumed the rubric was
an open scientific question I'd need the team to settle from scratch. Reading the 4D draft and
IPI-CHR-001 changed that: the dimensions are defined, the interpretive principles are written, and
the SOP carries real pass/fail numbers for SEC, intact mass, SPR, and Cell Display. What I need is
narrower — confirmation that I've mapped each warehouse assay onto the right dimension, and a
review of the derived profiles before any of them are published. I'd draft both and ask a scientist
to correct them. I'd keep this separate from the request above so the small ask isn't held up by
the larger one.

**A few decisions.** Whether to anchor the first version on IPI's own collection, as I'm
recommending; how cautious the tool should be in framing recommendations, given that these
are research-use-only reagents; any hosting or data-privacy constraints; and what we'd
consider good enough to launch publicly.

## What it would cost to run

The cost of a single question scales with how much reference data the tool pulls in and how
long its answer is. A simple question costs around two to three cents; a full Validation Profile
with citations costs closer to five to eight cents. At a hundred questions, that
is a few dollars in total — at that scale the questions are effectively free, and the real
cost is keeping the service running.

As usage grows, the cost stays manageable. A few design choices keep it that way:
precomputing the Validation Profiles in advance rather than generating them live,
routing simple questions to cheaper models and reserving the most capable one for hard
analysis, caching the parts of each request that don't change, and pulling facts from the
databases directly rather than asking the model to produce them.

## Risks

The largest open question isn't technical — it's timing. The 4D framework is still an unpublished
draft, so a public assistant explaining it would put our own contribution into the world ahead of
the paper. I'd want a decision early on whether the first public release can describe the framework
or should stay on already-public ground. I've built the boundary so this is a configuration change
rather than a rewrite: pre-publication content lives in a separate index the public build cannot
reach, so whichever way the decision goes, the content is already written and correct.

There's one place where two of our goals point in different directions, and I'd rather raise it now
than discover it late. Ranking commercial antibodies by validation status needs a single number to
sort on, and the 4D framework deliberately declines to produce one — it holds that partial or
conflicting findings should stay visible rather than being folded into an aggregate score. Shipping
a composite score would contradict our own published position in a product built to represent it. I
think the answer is to rank on a dimension the user picks, so they can see what was and wasn't
assessed, but that's a scientific call rather than mine.

The stages that reach beyond our own collection also carry a different kind of risk, and it isn't
technical. Ranking and recommending means making public statements about other companies' products,
so the framing matters: "IPI has no evidence that this antibody was validated for IHC" is
defensible in a way that "this antibody is poorly validated" is not, and the citation and abstention
discipline is what keeps answers on the right side of that. CiteAb's data is also commercially
licensed, and a ranking is a derived work, so I'd want the terms confirmed before building rather
than after. The coverage gap for third-party antibodies is real and is handled by abstaining rather
than guessing.
Accuracy is enforced by an evaluation harness that holds back any release that fails its
checks. Third-party licensing is resolved before the market-wide phase. And because these
are research reagents, the tool would carry clear research-use-only framing and would not
offer clinical guidance.

There's also a fair question about what happens if I'm not the one maintaining this, since
I'd be setting it up as an intern. I'd design for that from the start. The Google Cloud project would
belong to IPI rather than to me, so access and billing stay with the institute. The whole
setup would be defined in code and written up in a short runbook, so it's reproducible and
readable rather than locked in my head. The stack — Google Cloud, Python, Postgres — is standard
enough that any future developer or contractor could pick it up, and the managed services
handle most of the day-to-day upkeep. As a pilot, the stakes stay low until it has proven
worth investing in further.

## Summary of requests

To begin, I'm requesting:

Nothing here blocks me from starting — the first stage needs none of it. These are what the
stages after it depend on, listed roughly in the order I'd need them.

- An afternoon of a scientist's time to review and sign off the validation explainers.
- A pilot list of 10 to 20 already-public antibodies approved for release, with the fields
  that may be shown. This replaces the release-status filter I'd hoped to find in Benchling
  and had to create instead.
- Time from the science team to confirm the assay-to-dimension mapping and review derived
  Validation Profiles before publication.
- A small operating budget — a ceiling of about $50 a month, likely far less, especially in
  the first year.
- When we're ready to go live, help from IT to set up an IPI-owned Google Cloud project and
  own its billing — I can build locally at no cost until then.
- Access to the Addgene data and permission to ingest the public website content.
- Support to request a CiteAb quote and fund it when we reach the market-wide phase.
- Direction on how cautious the tool should be and on any hosting or privacy constraints.
