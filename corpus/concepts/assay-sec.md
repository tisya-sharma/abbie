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
  - label: IPI-CHR-001, internal antibody QC standard — grounds the description of IPI's own process. No criteria or record values are reproduced.
status: draft
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
a porous column. Larger species travel a shorter path through the pores and elute first, so a
preparation's composition appears as a series of peaks ordered by size. For an antibody
preparation the question it answers is what fraction of the material is the intended monomer and
what fraction is something else.

The something else is usually aggregate. Antibodies can associate into dimers and higher-order
species during expression, purification, concentration, freezing, or storage, and aggregation is
not visible from concentration or yield measurements. A preparation can be at the expected
concentration and still be substantially aggregated.

Aggregation matters beyond tidiness. Aggregated antibody has more binding sites presented
together, so it engages targets with higher apparent avidity than the monomer does, which
distorts affinity measurements and can produce binding signal that the monomeric reagent would
not reproduce. It also tends to raise background and to vary between preparations, which makes it
a direct contributor to lot-to-lot inconsistency.

SEC is therefore a **molecular integrity** measurement, and at IPI it runs on every batch of every
antibody, at small scale and again after scale-up. It is a property of the preparation rather
than of the antibody design, which is why it has to be repeated per batch rather than inherited
from an earlier one.

What SEC does not do is say anything about binding. A perfectly monomeric preparation may bind
nothing at all, or bind the wrong thing. **Integrity** is the foundation the other dimensions rest
on, not a substitute for them.
