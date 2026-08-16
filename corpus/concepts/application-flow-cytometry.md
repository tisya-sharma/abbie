---
id: application-flow-cytometry
title: Flow cytometry as an application
aliases:
  - flow cytometry
  - FACS
  - cell sorting
  - surface staining
  - gating
  - what does the gate show
ask: What does flow cytometry actually establish?
provenance: summarized
sources:
  - label: "Cossarizza A, Chang HD, Radbruch A, et al. Guidelines for the use of flow cytometry and cell sorting in immunological studies (third edition). Eur J Immunol. 2021;51(12):2708-3145."
    url: https://doi.org/10.1002/eji.202170126
    short: "Cossarizza 2021"
    journal: "Eur J Immunol"
    title: "Guidelines for the use of flow cytometry and cell sorting in immunological studies (third edition)"
    depth: full-text
  - label: "Andersen MN, Al-Karradi SN, Kragstrup TW, et al. Elimination of erroneous results in flow cytometry caused by antibody binding to Fc receptors on human monocytes and macrophages. Cytometry A. 2016;89(11):1001-1009."
    url: https://doi.org/10.1002/cyto.a.22995
    short: "Andersen 2016"
    journal: "Cytometry A"
    title: "Elimination of erroneous results in flow cytometry caused by antibody binding to Fc receptors on human monocytes and macrophages"
    depth: full-text
status: sourced
reviewed_by:
clearance: public
level: core
requires:
  - application-specificity
leads_to:
  - controls-in-validation
  - selectivity
# Rendered into the downloadable checklist, never into the model's context.
# Every item here is conditional on the sample rather than universal, which is
# the whole difficulty of writing a checklist for this application at all.
checklist:
  - item: Topology of the target established before staining an intact cell
    proves: The epitope faces outward, so an absent signal is a real absence
  - item: Effect of the dissociation method on the markers being measured considered
    proves: A missing surface protein was not cut off during sample preparation
  - item: Fc receptor blocking used where myeloid cells are present, and omitted where surface immunoglobulin is the target
    proves: Signal came through the binding site, without breaking the panel it was meant to protect
  - item: Isotype and lot of any control antibody recorded
    proves: Background was attributed to something reproducible rather than to one vial
  - item: Viability stain included in the panel
    proves: The bright rare population is live cells rather than dead ones taking up everything
  - item: Antibody titrated on the cells actually being used
    proves: Background belongs to the sample, not to more antibody than it needed
  - item: Gate set from a control rather than from an isotype tube or the eye
    proves: The boundary between negative and positive came from this panel
---

Flow cytometry does not take the cell apart. A suspension of intact cells is pushed single file
past a laser, and the instrument records for each cell that goes by how much fluorescence it
carried. Tens of thousands of cells, one measurement each, and the antibody met every one of
them while it was still whole.

Because the cell is whole, only the part of the target facing outward is available. Reaching
something on the inside means fixing and permeabilizing first, which is the same chemistry an
imaging experiment uses and is not free in the other direction either, since the stronger
permeabilization needed for nuclear targets can shrink cells and cost surface staining
intensity.

Whole is not the same as untouched, and this is where the method's apparent gentleness misleads.
Getting solid tissue into a suspension takes enzymes that can cleave off the very markers being
measured, including lineage-defining ones. The antibody can move its own target as well, since
binding some receptors drives them off the surface within minutes of the stain.

A whole cell can also hold an antibody by its tail rather than its binding site, though far less
generally than the warning usually implies. In one comparison across five donors, isotype
controls that should have bound nothing raised the signal on monocytes roughly threefold, while
one isotype did not bind them at all, T cells carry no receptor for the tail in the first place,
and two lots of the same clone behaved differently. Blocking helps and is not universal advice,
because the same block interferes with staining immunoglobulin on B cells.

Cells that died before reaching the instrument bind antibody without specificity and fluoresce
more on their own, which is why a viability stain is treated as essential rather than optional.

Where positive begins is then a decision rather than an observation, and the usual control is
narrower than its reputation. Leaving one antibody out of an otherwise complete panel measures
how much the other colors spill into that channel, and it is blind to the nonspecific binding of
the very antibody it left out. What flow cytometry establishes is how many cells in one
suspension carried signal past a line someone drew, under one staining condition. The
literature's own position on where such lines belong is that they have to be determined for each
test system independently.
