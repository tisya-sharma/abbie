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

IPI organizes validation evidence along four foundational dimensions: **molecular integrity**,
**target engagement**, **selectivity**, and **experimental readout**. Together they describe the distinct
properties that determine whether an antibody can be relied on, and separating them makes it
possible to say precisely what has been established and what has not.

The dimensions are ordered by dependency rather than importance. **Integrity** establishes that
the reagent is defined and reproducible. **Engagement** establishes that it binds the intended
target. **Selectivity** establishes that the binding is attributable to that target rather than a
relative. **Readout** establishes that it produces an interpretable result in a specific
application, with appropriate controls.

None of the four is settled by any one experiment, and no experiment covers all of them. A surface
plasmon resonance (SPR) measurement speaks to **engagement** and says nothing about **readout**. A clean
Western blot speaks to **readout** and only weakly to **selectivity**. Evidence therefore has to be
assembled across dimensions and interpreted together, in light of the application the antibody is
actually intended for.

The dimensions organize evidence by the property it supports, not by the experimental approach
used to generate it. The question is never which methods were run, but which foundational
properties those methods establish — and consequently, which remain open.

The practical consequence is that IPI treats some widely used approaches, including genetic
perturbation, independent antibodies, and expression correlation, as evidence-strengthening approaches rather than as dimensions of their own. They raise confidence in the interpretation
of evidence generated in a given assay and system context; they are not separate dimensions. A
knockout control is not a separate kind of validation, it is what makes an immunofluorescence
result attributable.
