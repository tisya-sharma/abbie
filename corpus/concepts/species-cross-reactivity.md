---
id: species-cross-reactivity
title: Why an antibody validated in one species may not work in another
aliases:
  - species cross-reactivity
  - does this antibody work in mouse
  - will this antibody work in my model organism
  - cross-species reactivity
  - species reactivity
ask: Does an antibody validated in one species work in another?
provenance: summarized
sources:
  - label: "Pruvost T, Mathieu M, Dubois S, Maillère B, Vigne E, Nozach H. Deciphering cross-species reactivity of LAMP-1 antibodies using deep mutational epitope mapping and AlphaFold. mAbs. 2023;15(1):2175311."
    url: https://doi.org/10.1080/19420862.2023.2175311
    short: "Pruvost 2023"
    journal: "mAbs"
    title: "Deciphering cross-species reactivity of LAMP-1 antibodies using deep mutational epitope mapping and AlphaFold"
  - label: "Hu Y, Gao C, McKenna W, et al. Cross-Species Epitope Sequence Analysis for Discovery of Existing Antibodies Useful for Phospho-Specific Protein Detection in Model Species. Int J Mol Sci. 2025;26(2):558."
    url: https://doi.org/10.3390/ijms26020558
    short: "Hu 2025"
    journal: "Int J Mol Sci"
    title: "Cross-Species Epitope Sequence Analysis for Discovery of Existing Antibodies Useful for Phospho-Specific Protein Detection in Model Species"
status: draft
reviewed_by:
clearance: public
level: core
requires:
  - what-is-a-target
leads_to:
  - selectivity
  - application-specificity
---

An antibody grips one small patch on its target. The corresponding protein in a different animal
is not quite the same protein: orthologs, meaning the version of a gene's product found in
another species, accumulate sequence differences over evolutionary time. If those differences
fall where the antibody makes contact, it stops recognizing the protein. That contact patch is
not always one continuous run of sequence, since residues far apart in the chain can be brought
together when the protein folds, so what decides the outcome is whether the contacted residues
are conserved rather than whether the region looks similar overall.

How little difference it takes can be striking. Two antibodies against human LAMP-1 were mapped
residue by residue, then compared against predicted structures of the protein in other species.
Both epitopes in the mouse version carried multiple changes. In the macaque version, one
substitution was enough to hinder recognition by one antibody and two were enough for the other.
A macaque is a close primate relative, and that closeness did not preserve binding.

Sequence comparison is therefore used to predict where an existing antibody might transfer.
Software built for this aligns a protein against its orthologs and reports whether the site an
antibody targets is conserved, an approach used to shortlist mammalian phospho-specific
antibodies that might detect the corresponding sites on fly proteins. The authors present those
as predictions of what might be useful, a candidate list for testing rather than established
reactivity.

IPI's own definition puts species alongside application among the things validation attaches to,
rather than to the antibody in the abstract. Evidence that an antibody detects your target in
human samples is evidence about human samples. For work in another species, look for evidence
generated in that species, with the controls that make the signal attributable there.

This tells you whether the antibody binds at all in a new species. It does not tell you whether
the binding is selective there, which is a separate question: a different organism carries a
different set of related proteins that the same antibody might also bind.
