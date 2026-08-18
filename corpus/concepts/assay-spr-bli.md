---
id: assay-spr-bli
title: SPR and BLI binding measurements
aliases:
  - SPR
  - BLI
  - surface plasmon resonance
  - biolayer interferometry
  - binding kinetics
  - affinity measurement
ask: What do SPR and BLI measure?
provenance: ipi-authored
sources:
  - label: IPI-CHR-001, internal antibody QC standard — grounds the description of IPI's own process. No criteria or record values are reproduced.
    depth: full-text
  - label: "Institute for Protein Innovation. Quality. proteininnovation.org/quality/. IPI's own public statement of its antibody quality and validation standards, which describes these tiers and assays directly."
    url: https://proteininnovation.org/quality/
    short: "IPI Quality"
    title: "Quality"
    depth: full-text
  - label: IPI 4D framework, internal draft — defines the dimensions this concept names. No manuscript text is reproduced.
    depth: full-text
status: sourced
reviewed_by:
clearance: public
level: advanced
requires:
  - target-engagement
leads_to:
  - assay-cell-display
  - what-is-binding
  - selectivity
---

Surface plasmon resonance (SPR) and biolayer interferometry (BLI) both measure binding as it
happens, without labeling either partner. One binding partner is immobilized on a sensor surface,
the other is in solution, and the instrument reports the accumulating mass at the surface
in real time. The resulting curve has a rising association phase while the analyte binds and a
falling dissociation phase once buffer alone surrounds the sensor and the bound analyte releases
into it.

Because the measurement is kinetic rather than an endpoint, it separates two things a single
binding number conflates. The association rate describes how quickly the complex forms; the
dissociation rate describes how quickly it falls apart. Their ratio gives the equilibrium
dissociation constant, the affinity. Two antibodies can share an affinity while behaving quite
differently, since the same ratio can arise from a fast pair of rates or a slow one, which is why
IPI's reading of an SPR result rests on the dissociation rate as well as on the affinity.

This is **target engagement** evidence, and among the most direct kinds available: it establishes
that the antibody binds the intended antigen, and quantifies how well. At IPI, SPR runs on
small-scale material as one of the two activity screens that decide which antibodies are worth
scaling up.

Its limitation is the same one that makes it clean. The measurement is usually performed against
purified antigen on an artificial surface, which is the simplest region of IPI's Validation Map:
no competing proteins, no membrane, no cellular context. Binding measured there establishes
**engagement** and says nothing about **selectivity**, since nothing else was present to bind, and
nothing about **readout** in any real application.
