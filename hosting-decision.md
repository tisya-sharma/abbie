# Abbie: Hosting Architecture on Google Cloud

Tisya Sharma. Reference document — the platform decision is settled.

**Decision: Abbie runs on Google Cloud**, as a container on Cloud Run with a managed Postgres
database. This document explains why the application needs its own environment, what the
component pieces are and which Google Cloud service provides each, and the reasoning behind
the two choices that shape the architecture — a container rather than a serverless function,
and a managed database rather than a self-run one.

## 1. Why Abbie needs its own environment

Our website runs on WordPress. WordPress hosting serves web pages — it cannot run a custom
Python application with a database, background jobs, and AI calls behind it. That is true of
any approach we take; Abbie is a real piece of software and needs its own application
environment.

So the question was never "cloud or no cloud." It was only ever which environment, and that
is now settled.

## 2. What Abbie needs

- Run a **Python (FastAPI)** application.
- **PostgreSQL with `pgvector`** — one database holding the antibody records and the vectors.
- A **scheduler** to rebuild the published extract from Benchling, re-sync Addgene, and
  re-crawl site content.
- **Secrets storage** for the model API key and database credentials.
- An **HTTPS endpoint** the WordPress chat widget can call.
- **Very low volume** — on the order of 100 questions. Near-zero cost matters far more than
  scale; ideally compute costs nothing when idle.
- **Token streaming**, so answers appear as they're written rather than after a long pause.
- To be **definable as code** and **handed off** — I'm one person, and an intern. Nothing
  should live only in my head.
- **A real data boundary.** The source is IPI's Benchling warehouse — a read-only Postgres
  mirror, scoped per credential by row-level security to the projects that user can read. Within
  those projects it returns everything: unpublished programs, draft results, archived records,
  and a `user` table carrying staff names and emails. The public assistant must never read it
  directly. Abbie serves from a separate database holding only approved records, rebuilt on a
  schedule through a column allowlist. That extract is the boundary, and the point of building
  it that way is that it can be reviewed and signed off rather than trusted.
- **A dedicated Benchling service account** for the sync job, scoped to the minimum set of
  projects — not a personal credential. Benchling warehouse credentials are static, long-lived,
  and usable by anyone who holds them, so they belong in Secret Manager and nowhere else.

## 3. Primer: three ideas behind the design

**IaaS vs. PaaS vs. serverless.** IaaS (a raw VM) means we manage the OS, patching, and
scaling — maximum control, maximum work. PaaS ("here's my container, run it") hands that to
the vendor. Serverless goes further: code runs only when a request arrives, billed per
request. We want the managed end of this spectrum, because the work we avoid is work I'd
otherwise do alone.

**Scale-to-zero.** If nothing runs when nobody is asking, idle costs nothing. At ~100
questions/month Abbie is idle essentially always, so this is worth a lot.

**The database is the cost floor.** Compute scales to zero. A managed database generally
doesn't — it sits there, running, billing. That is why the database is the main line item in
our budget while everything else rounds to nothing.

## 4. Why a container, not a serverless function

This is the choice that shapes everything else.

FastAPI is a **long-running ASGI server**. That single fact splits the options:

- **Serverless functions** (Cloud Functions) need an adapter to run FastAPI at all, typically
  cap requests at short timeouts, and make Python token-streaming awkward.
- **Containers** (Cloud Run) run FastAPI natively with no adapter, **stream natively**, have
  no short request ceiling, and still **scale to zero**.

Cloud Run gives us the serverless benefits — pay per request, nothing running when idle —
without the function-shaped constraints. It also bundles the HTTPS endpoint, TLS, and
autoscaling, so there's no separate gateway to configure.

Two further benefits worth naming:

**Portability.** The same container image runs anywhere — Cloud Run, another cloud's container
service, or a simple managed host. Our lock-in lives in the deployment configuration, not in
the application. Moving platforms would mean rewriting config, not rebuilding Abbie.

**Local-first development.** The same image runs on my laptop. I build and test everything
locally (FastAPI plus Postgres with `pgvector` in Docker) at zero cost, and deploying to
Google Cloud is a deployment step rather than a port.

## 5. The components, and which service provides each

**1. Compute.** Something has to execute the Python when a question arrives. This is the only
piece that *is* Abbie; everything else supports it. → **Cloud Run**

**2. HTTPS front door.** The widget in someone's browser needs a stable, TLS-terminated URL
with CORS configured, and — because it's public — rate limiting so nobody can run up our model
bill. → **bundled into Cloud Run**

**3. Database.** Postgres with `pgvector`, holding the antibody records and the vector
embeddings — the source of truth the model reads from instead of inventing. → **Cloud SQL for
PostgreSQL**, reached through the **Cloud SQL Auth Proxy** for secure, pooled connections

**4. Scheduler.** Benchling and Addgene records change, and so does the website; something has
to rebuild the published extract and re-crawl on a cadence. → **Cloud Scheduler** triggering
**Cloud Run Jobs**

**5. Secrets.** The model API key and database credentials can't live in the repo or on disk.
→ **Secret Manager**

**6. Identity and permissions.** The app should read its own secret and reach its own database
and nothing else. This is also how CI deploys without us storing long-lived cloud keys. → **IAM
service accounts** + **Workload Identity Federation**

**7. Logs, metrics, alarms.** When Abbie errors or answers badly we need the trace, plus
latency and cost visibility. → **Cloud Logging** + **Cloud Monitoring**

**8. Cost guardrail.** A runaway loop or abuse spike should alert us, not surprise us on the
invoice. → **Cloud Billing budgets and alerts**

Supporting pieces: **Artifact Registry** for the container image, and **Cloud Storage** for
Terraform state and cached ingest artifacts.

### The stack at a glance

| Component | Service |
|---|---|
| Compute | **Cloud Run** — scales to zero, streams natively |
| HTTPS front door | bundled in Cloud Run (TLS, stable URL, autoscaling) |
| Database | Cloud SQL for PostgreSQL + `pgvector` |
| Connection pooling | Cloud SQL Auth Proxy |
| Scheduler | Cloud Scheduler → Cloud Run Jobs |
| Secrets | Secret Manager |
| Identity | IAM service accounts + Workload Identity Federation |
| Logs & metrics | Cloud Logging + Cloud Monitoring |
| Cost guardrail | Cloud Billing budgets and alerts |
| Image registry | Artifact Registry |
| Terraform state | Cloud Storage |
| Infrastructure as code | Terraform |

Deliberately **not** used: GCE VMs and GKE/Kubernetes (far too heavy for this traffic), and
Vertex AI (we call a model provider's API rather than hosting models ourselves).

### Staff surfaces, added later

The public widget is the first surface but not the only one. Internal staff reach the same
antibody tools through **ChatGPT** and **Slack**, which arrive at Stage 4 of
[roadmap.md](roadmap.md) rather than with the initial deploy. Neither changes the platform
decision — both are additional Cloud Run services over the same database:

| Component | Service |
|---|---|
| MCP server (Streamable HTTP + OAuth) — serves ChatGPT as an MCP connector | a second **Cloud Run** service |
| Slack app (Bolt) — Slack is not an MCP client, so it calls the tools directly | a third **Cloud Run** service |

Both are thin transport adapters over one shared, typed tool library, not reimplementations, so
they add deployment surface rather than architecture. They also raise one question the public
widget does not: if staff surfaces expose unpublished records, tool results flow into the hosted
model as context. That is a data-residency decision, not a hosting one — see architecture.md, Decisions
for the team #5.

## 6. The database: one Postgres is right, but "anywhere" isn't

A fair question: why not just run a Postgres somewhere cheap?

**"One instance" is right — "anywhere" is what fails.** One Postgres holding both the antibody
records and the vectors is exactly our design; at ~100 questions, replicas, multi-region, or
sharding would be textbook overengineering. We are not overbuilding the database. But that one
instance has six requirements, and most run-it-anywhere options fail at least one:

1. **It's one of eight pieces, not the system.** A database doesn't run the API, schedule the
   ingestion job, store secrets, serve HTTPS, or collect logs.
2. **`pgvector` is a hard filter.** Our prose retrieval needs the extension, and many cheap or
   shared Postgres hosts don't permit installing extensions at all. "Any Postgres" is
   factually false — it must be one where we can enable pgvector. This alone eliminates most
   run-it-anywhere candidates.
3. **Connection pooling is mandatory with autoscaling compute.** Cloud Run can run many
   instances at once, and a small Postgres allows only ~50–100 connections. Without a pooler
   we exhaust them under exactly the conditions we wanted to handle. The Cloud SQL Auth Proxy
   covers this.
4. **Backups, durability, recovery.** A hand-run instance means we own backups, point-in-time
   recovery, patching, and failover. If it dies, the antibody index and the precomputed
   Validation Profiles die with it. Cloud SQL gives us automated backups by default.
5. **Security posture.** Internet-exposed Postgres is scanned and brute-forced constantly. We
   want it reached through the Auth Proxy with credentials in Secret Manager — not an open
   port and a password in a `.env` file.
6. **Reproducibility and ownership.** A hand-clicked database isn't in Terraform, isn't
   documented, and may not sit on an IPI-owned project. Nobody could recreate it, and when I
   leave nobody would know how it was configured.

Latency is a seventh factor but a minor one: several round-trips per question, ~5ms
co-located versus a few hundred milliseconds cross-provider. Worth doing right; not the
argument that decides it.

**Two rules follow:** co-locate the database with the compute (same project and region), and
treat `pgvector` support plus connection pooling as non-negotiable.

**One thing to revisit later:** Cloud SQL does not scale to zero, so it's a steady monthly cost
whether or not anyone is asking questions. If that becomes a concern, serverless Postgres
options that scale to zero (Neon and similar) support `pgvector`, include pooling, and run in
Google Cloud regions so they'd still co-locate. Not worth the second vendor today — worth
knowing the option exists.

## 7. Cost

- **$0 while developing locally** — nothing runs on Google Cloud until we deploy.
- **Once deployed, roughly $15–40/month**, of which the Cloud SQL instance is the bulk.
- Cloud Run, Secret Manager, Scheduler, Artifact Registry, and logging are all ~$0 at our
  volume.
- The model API at ~100 questions is a few dollars.
- Cloud SQL has no extended free tier, so treat it as a steady cost from deployment.
- A billing alert goes on from day one.

## 8. Anticipated questions

**Why not just put it on the website's hosting?**
WordPress hosting serves web pages. It can't run a Python application with a database and AI
calls. True of any approach — the chatbot needs its own home regardless of platform.

**Isn't a cloud platform overkill for ~100 questions?**
It would be if we used the heavy parts — VM fleets, Kubernetes, hand-built networking. We
aren't. We need a container that runs on demand, a small database, a scheduler, and a secrets
store. Everything else rounds to zero at our volume.

**Aren't we locking ourselves in?**
Barely. The app is a standard Python container and Postgres is Postgres — the lock-in lives in
the Terraform configuration, not the code. Moving platforms would mean rewriting deployment
config, not rebuilding Abbie. That's a days-long task, not a rebuild.

**Who maintains this after you leave?**
Designed for, not hoped for: the project belongs to IPI, the setup lives in Terraform plus a
runbook, and the stack (Google Cloud, Python, Postgres) is standard enough that any developer
or contractor can pick it up.

**Why not run it on our own servers?**
Someone would have to patch, secure, back up, and monitor it — and that's me, until I'm gone.
And because the public assistant only ever reads the approved extract, on-prem buys little
privacy benefit to offset that cost — the boundary is the extract, not the hosting location.

## 9. Next steps

1. Build locally first — no cost, and no setup required from IPI.
2. Stand up an IPI-owned Google Cloud project, with IT owning it and the billing, when we're
   ready to go live.
3. Set a Cloud Billing budget alert on day one.
4. Define everything in Terraform from the start so the setup is reproducible and
   handoff-able.
