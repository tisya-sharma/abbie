---
id: paralogs-and-isoforms
title: Why a signal is hard to attribute to one protein
aliases:
  - what is a paralog
  - related proteins
  - how do I know the signal is my protein
  - cross-reactivity with family members
ask: How do I know a signal comes from my protein?
provenance: summarized
sources:
  - label: "Uhlén M, Bandrowski A, Carr S, et al. A proposal for validation of antibodies. Nat Methods. 2016;13(10):823-827."
    url: https://doi.org/10.1038/nmeth.3995
    short: "Uhlén 2016"
    journal: "Nat Methods"
    title: "A proposal for validation of antibodies"
status: draft
reviewed_by:
clearance: public
level: core
requires:
  - what-is-a-target
leads_to:
  - selectivity
  - genetic-perturbation-controls
---

A band on a blot or a glow in a cell is a signal. It does not arrive labeled with which protein
produced it, and that is the whole difficulty.

Proteins come in families. Paralogs are related proteins encoded by different genes in the
same family, often sharing substantial stretches of sequence. An antibody raised against one
family member can bind its relatives, because the patch it recognizes may be present on several
of them. Deciding that an observed signal came from the intended protein rather than a relative
is a question the signal itself cannot answer.

This is the case genetic evidence is specifically suited to. Removing or reducing the target
protein and repeating the experiment provides a direct link between the gene, the protein, and
what the antibody detects, and the approach is described as particularly useful for examining
specificity for proteins that come from related genes — that is, members of multigene families.

A known limit worth stating plainly. Attribution among *isoforms* or splice variants of the
same gene is a harder problem than attribution among paralogs, and it is not solved by the same
evidence. Deleting a gene removes all of its isoforms at once, so a knockout cannot distinguish
which isoform an antibody was detecting. This corpus does not currently carry a sourced account
of how isoform-level attribution is established.
