---
id: four-dimensional-framework
title: How IPI organizes validation evidence
aliases:
  - four dimensions
  - IPI's validation framework
  - levels of validation
provenance: ipi-authored
sources:
  - label: D. Moshinsky, chatbot kickoff notes, 14 July 2026
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
  - five-pillars-iwgav
---

IPI organizes validation evidence along four foundational dimensions: Molecular Integrity,
Target Engagement, Selectivity, and Experimental Readout. Together they describe the distinct
properties that determine whether an antibody can be relied on, and separating them makes it
possible to say precisely what has been established and what has not.

The dimensions are ordered by dependency rather than importance. Integrity establishes that
the reagent is defined and reproducible. Engagement establishes that it binds the intended
target. Selectivity establishes that the binding is attributable to that target rather than a
relative. Readout establishes that it produces an interpretable result in a specific
application, with appropriate controls.

None of the four is settled by any one experiment, and no experiment covers all of them. An
SPR measurement speaks to Engagement and says nothing about Readout. A clean Western blot
speaks to Readout and only weakly to Selectivity. Evidence therefore has to be assembled
across dimensions and interpreted together, in light of the application the antibody is
actually intended for.

This differs from organizing evidence by the experimental approach used to generate it, which is
how the field's widely adopted five-pillar proposal is structured. The question is not which
methods were run, but which foundational properties those methods support — and consequently,
which remain open.

The practical consequence is that approaches the five-pillar framing treats as validation
strategies in their own right — genetic perturbation, independent antibodies, expression
correlation — are treated here as **evidence-strengthening approaches** instead. They raise
confidence in the interpretation of evidence generated in a given assay and system context; they
are not separate dimensions. A knockout control is not a fifth kind of validation, it is what
makes an immunofluorescence result attributable.
