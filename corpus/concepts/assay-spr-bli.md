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
status: draft
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
the other flows past in solution, and the instrument reports the accumulating mass at the surface
in real time. The resulting curve has a rising association phase while the analyte binds and a
falling dissociation phase after it is washed away.

Because the measurement is kinetic rather than an endpoint, it separates two things a single
binding number conflates. The association rate describes how quickly the complex forms; the
dissociation rate describes how quickly it falls apart. Their ratio gives the equilibrium
dissociation constant, the affinity. Two antibodies can share an affinity while behaving quite
differently, and for most applications the dissociation rate is the more practically important of
the two, because it determines whether the complex survives the washes an assay puts it through.

This is Target Engagement evidence, and among the most direct kinds available: it establishes
that the antibody binds the intended antigen, and quantifies how well. At IPI, SPR runs on
small-scale material as one of the two activity screens that decide which antibodies are worth
scaling up.

Its limitation is the same one that makes it clean. The measurement is usually performed against
purified antigen on an artificial surface, which is the simplest region of IPI's Validation Map:
no competing proteins, no membrane, no cellular context. Strong binding there establishes
Engagement and says nothing about Selectivity, since nothing else was present to bind, and
nothing about Readout in any real application.
