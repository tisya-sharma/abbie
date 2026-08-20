---
id: assay-cell-display
title: Cell display binding assays
aliases:
  - cell display
  - cell surface binding
  - does it bind on cells
  - polyreactivity screening
ask: What does a cell display assay show?
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
  - target-engagement
leads_to:
  - assay-spr-bli
  - selectivity
  - paralogs-and-isoforms
---

A cell display assay presents the antigen on the surface of cells rather than purified on
a sensor chip. Cells are transfected to express the target, incubated with the antibody, labeled
with a secondary reagent, and read by flow cytometry, so binding is measured per cell across a
population.

The reason to do this rather than rely on purified antigen is context. A membrane protein
displayed on a cell sits in a lipid bilayer, is glycosylated as the cell glycosylates it, and
adopts a conformation that a purified fragment may not reproduce. Binding measured in one system
does not by itself establish binding in another, so an antibody that binds purified antigen has
not thereby been shown to bind the same antigen on a cell, and the reverse holds too.
Cell display therefore sits further along the biological system axis of IPI's Validation Map
than a biochemical binding measurement does, while remaining an engineered expression system
rather than a native one.

The format supports two distinct questions. Run against the intended target, it is
**target engagement** evidence in a more physiological setting. Run against related family
members expressed separately in the same system, it becomes a cross-reactivity experiment and
therefore **selectivity** evidence, which is the use IPI puts particular weight on, because
binding a paralog is a failure mode that a purified-antigen run against the intended target
alone, with no relative present to bind, cannot reveal.

The assay also surfaces polyreactivity, the tendency of some antibodies to stick broadly and
non-specifically. Signal appearing against the controls rather than only against the antigen
identifies a reagent whose apparent binding elsewhere cannot be trusted, and IPI excludes such
antibodies from further consideration rather than attempting to work around them.
