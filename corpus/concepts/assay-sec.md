---
id: assay-sec
title: Size-exclusion chromatography
aliases:
  - SEC
  - size exclusion
  - aggregation testing
  - is my antibody aggregated
ask: What does size-exclusion chromatography tell you?
provenance: ipi-authored
sources:
  - label: IPI-CHR-001, internal antibody QC standard. Grounds the description of IPI's own process. No criteria or record values are reproduced.
    depth: full-text
  - label: "Institute for Protein Innovation. Quality. proteininnovation.org/quality/. IPI's own public statement of its antibody quality and validation standards, which describes these tiers and assays directly."
    url: https://proteininnovation.org/quality/
    short: "IPI Quality"
    title: "Quality"
    depth: full-text
  - label: IPI 4D framework, internal draft. Defines the dimensions this concept names. No manuscript text is reproduced.
    depth: full-text
status: sourced
reviewed_by:
clearance: public
level: advanced
requires:
  - molecular-integrity
leads_to:
  - antibody-characterization
  - assay-mass-spectrometry
  - reagent-reproducibility
---

Size-exclusion chromatography (SEC) separates molecules by hydrodynamic size as they pass through
a porous column. Larger species are excluded from more of the pore volume, so they take a shorter
path through the column and elute first, and a preparation's composition appears as a series of
peaks ordered by size. For an antibody preparation the question it answers is what fraction of the
material is the intended monomer and what fraction is something else.

The something else that matters here is aggregate. Antibodies can associate into dimers and
higher-order species, and aggregation is not visible from concentration or yield measurements. A
preparation can be at the expected concentration and still be substantially aggregated.

Aggregation matters beyond tidiness. Aggregated antibody has more binding sites presented
together, so it engages targets with higher apparent avidity than the monomer does, which
distorts affinity measurements and can produce binding signal that the monomeric reagent would
not reproduce. It also varies between preparations, which makes it a direct contributor to
lot-to-lot inconsistency.

SEC is therefore a **molecular integrity** measurement, and at IPI it runs on every batch of every
antibody, at small scale and again after scale-up. It is a property of the preparation rather
than of the antibody design, which is why it has to be repeated per batch rather than inherited
from an earlier one.

What SEC does not do is say anything about binding. A perfectly monomeric preparation may bind
nothing at all, or bind the wrong thing. **Integrity** is the foundation the other dimensions rest
on, not a substitute for them.
