---
id: assay-mass-spectrometry
title: Intact mass analysis
aliases:
  - mass spec
  - intact mass
  - molecular weight verification
  - is this the right antibody
ask: What does intact mass analysis confirm?
provenance: ipi-authored
sources:
  - label: IPI-CHR-001, internal antibody QC standard — grounds the description of IPI's own process. No criteria or record values are reproduced.
  - label: "Institute for Protein Innovation. Quality. proteininnovation.org/quality/. IPI's own public statement of its antibody quality and validation standards, which describes these tiers and assays directly."
    url: https://proteininnovation.org/quality/
    short: "IPI Quality"
    title: "Quality"
  - label: IPI 4D framework, internal draft — defines the dimensions this concept names. No manuscript text is reproduced.
status: draft
reviewed_by:
clearance: public
level: advanced
requires:
  - molecular-integrity
leads_to:
  - antibody-characterization
  - assay-sec
  - reagent-reproducibility
---

Intact mass analysis measures the molecular weight of the antibody chains directly and compares
each against the mass predicted from its sequence. Agreement is evidence that the molecule in the
vial is the molecule that was designed.

In practice the antibody is reduced before measurement, breaking the disulfide bonds that hold it
together so the heavy and light chains can be weighed separately. Measuring the chains
individually is more informative than measuring the assembled molecule: a discrepancy can be
localized to one chain, and a problem affecting only the light chain is not hidden inside a much
larger total.

The measurement is sensitive enough to be a real identity check rather than a formality. Mass
differences arising from a wrong construct, an incomplete sequence, an unexpected modification,
or a contaminating protein are all resolvable, and the comparison is against a theoretical value
computed from the sequence rather than against another sample.

This makes intact mass a **molecular integrity** measurement, and specifically the identity half of
it, where size-exclusion chromatography covers the purity half. At IPI it is performed after
scale-up alongside sequence verification of the plasmid, and both are required before an antibody
is distributed. IPI treats the pair as the antibody's sequence verification: the plasmid
establishes what was encoded, and matching each measured chain against its predicted mass
confirms that the antibody produced is that molecule.

Like all characterization, it says nothing about function. Confirming that the intended molecule
was made is what allows a later binding result to be attributed to that molecule, and it is
worth little on its own.
