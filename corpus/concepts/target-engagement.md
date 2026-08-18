---
id: target-engagement
title: Target Engagement
aliases:
  - engagement
  - does the antibody bind its target
  - binding
ask: What is target engagement?
provenance: ipi-authored
sources:
  - label: D. Moshinsky, chatbot kickoff notes, 14 July 2026
  - label: IPI 4D framework, internal draft — defines the framework these concepts state. No manuscript text is reproduced.
  - label: "Institute for Protein Innovation. Quality. proteininnovation.org/quality/. IPI's own public statement of its antibody quality and validation standards, which describes these tiers and assays directly."
    url: https://proteininnovation.org/quality/
    short: "IPI Quality"
    title: "Quality"
status: draft
reviewed_by:
clearance: public
level: core
requires:
  - what-is-a-target
  - what-is-binding
leads_to:
  - selectivity
  - assay-spr-bli
  - assay-cell-display
---

**Target engagement**, the second of IPI's four dimensions, is an antibody's capacity to bind the
target it is intended for. It is measured in a model system where the target is known to be present
and accessible, such as a HEK overexpression system, so that a binding signal can be interpreted
without ambiguity about whether the target was there to be bound.

Typical assays include surface plasmon resonance (SPR), biolayer interferometry (BLI), and cell
display. SPR and BLI measure the interaction directly and report kinetics and affinity against
purified protein. Cell display measures binding to target presented on a cell surface, which is
closer to the context most experiments care about. Each answers the same question at a different
level of biological complexity.

**Engagement** answers a deliberately narrow question: does the antibody bind its intended target
at all. Whether that binding is selective is a separate matter. An antibody can bind its
target well and also bind several related proteins, and an engagement measurement alone cannot
distinguish those cases. That is what selectivity addresses.
