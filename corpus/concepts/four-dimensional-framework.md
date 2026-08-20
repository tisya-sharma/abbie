---
id: four-dimensional-framework
title: How IPI organizes validation evidence
aliases:
  - four dimensions
  - IPI's validation framework
  - levels of validation
ask: How does IPI organize validation evidence?
provenance: ipi-authored
sources:
  - label: D. Moshinsky, chatbot kickoff notes, 14 July 2026
    depth: full-text
  - label: IPI 4D framework, internal draft. Defines the framework these concepts state. No manuscript text is reproduced.
    depth: full-text
  - label: "Institute for Protein Innovation. Quality. proteininnovation.org/quality/. IPI's own public statement of its antibody quality and validation standards, which describes these tiers and assays directly."
    url: https://proteininnovation.org/quality/
    short: "IPI Quality"
    title: "Quality"
    depth: full-text
status: sourced
reviewed_by:
clearance: public
level: core
requires:
  - antibody-validation
leads_to:
  - molecular-integrity
  - target-engagement
  - selectivity
  - experimental-readout
  - validation-map
  - validation-profile
  - fitness-for-purpose
---

IPI organizes validation evidence along four dimensions it treats as foundational:
**molecular integrity**, **target engagement**, **selectivity**, and **experimental readout**. Between
them they describe the distinct properties that determine whether an antibody can be relied on,
and separating them makes it possible to say precisely what has been established and what has not.

The dimensions are listed by what each one rests on rather than by importance, and that order
describes dependency between the properties rather than a sequence the experiments have to
follow. **Integrity** establishes that the reagent is defined, pure, and reproducible.
**Engagement** establishes that it binds the intended target. **Selectivity** establishes that the
binding is attributable to that target rather than an alternative one. **Readout** establishes
that it produces an interpretable result in a specific application, with appropriate controls.

No single validation method establishes all four dimensions. A surface plasmon resonance (SPR)
measurement supports **engagement**, while the evidence that an antibody works in a given
application comes from testing it in that application. A single band at the expected molecular
weight on a Western blot supports **readout** and is consistent with **engagement**, yet
confidence in **selectivity** stays moderate without further evidence, because an off-target
protein can migrate to a similar position. Evidence therefore has to be assembled across
dimensions and interpreted together, in light of the application the antibody is actually
intended for.

The dimensions organize evidence by the property it supports rather than by the experimental
approach used to generate it, while the assay and system context each finding came from is
preserved rather than discarded. The question is not which methods were run but which
foundational properties those methods inform, and consequently which remain open.

The practical consequence is that IPI treats some widely used approaches, including genetic
perturbation, independent antibodies, and expression correlation, as evidence-strengthening
approaches rather than as dimensions of their own. They raise confidence in the interpretation
of evidence generated in a given assay and system context; they are not separate dimensions. A
knockout control is not a separate kind of validation, it is what strengthens confidence that an
immunofluorescence signal can be attributed to the intended target, and even that conclusion
depends on which related proteins the system examined actually expresses.
