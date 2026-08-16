---
id: application-immunofluorescence
title: Immunofluorescence as an application
aliases:
  - immunofluorescence
  - IF
  - immunocytochemistry
  - ICC
  - immunostaining
  - what does the staining show
ask: What does immunofluorescence actually establish?
provenance: summarized
sources:
  - label: "Stadler C, Skogs M, Brismar H, et al. A single fixation protocol for proteome-wide immunofluorescence localization studies. J Proteomics. 2010;73(6):1067-1078."
    url: https://doi.org/10.1016/j.jprot.2009.10.012
    short: "Stadler 2010"
    journal: "J Proteomics"
    title: "A single fixation protocol for proteome-wide immunofluorescence localization studies"
  - label: "Schnell U, Dijk F, Sjollema KA, et al. Immunolabeling artifacts and the need for live-cell imaging. Nat Methods. 2012;9(2):152-158."
    url: https://doi.org/10.1038/nmeth.1855
    short: "Schnell 2012"
    journal: "Nat Methods"
    title: "Immunolabeling artifacts and the need for live-cell imaging"
  - label: "Stadler C, Rexhepaj E, Singan VR, et al. Immunofluorescence and fluorescent-protein tagging show high correlation for protein localization in mammalian cells. Nat Methods. 2013;10(4):315-323."
    url: https://doi.org/10.1038/nmeth.2377
    short: "Stadler 2013"
    journal: "Nat Methods"
    title: "Immunofluorescence and fluorescent-protein tagging show high correlation for protein localization in mammalian cells"
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
# These are the ways a stained image misleads before any control is read, and
# all of them are decided during sample preparation rather than at the scope.
checklist:
  - item: Fixation chemistry chosen for this target rather than inherited from the protocol
    proves: Cross-linking and alcohol dehydration were treated as different experiments, not defaults
  - item: Accessibility of the compartment the target occupies accounted for
    proves: The antibody could reach the place the result reports on
  - item: The target's own chemistry considered when the fixative was chosen
    proves: The preparation did not alter the protein out of recognition
  - item: Preparation checked for extraction or relocalization of the target
    proves: The pattern is where the protein sat, not where the protocol moved it
  - item: Localization corroborated by a method that uses no antibody
    proves: The pattern belongs to the protein rather than to the reagent
  - item: More than one compartment considered before a single location is reported
    proves: An expected location has not been mistaken for the only one
---

Immunofluorescence leaves the cell where it is. Nothing is pulled out and sorted by size or
weight. The cell is fixed in place on a slide, opened up so that reagents can get inside, and a
fluorescent antibody is sent in to find one protein wherever it happens to sit. What comes back
is an image of a cell with some part of it lit up.

Fixation is a choice between two chemistries and it is not a neutral one. A sample can be
dehydrated with an alcohol such as methanol or ethanol, or it can be cross-linked with
paraformaldehyde and then permeabilized with a detergent. A systematic comparison across a panel
of human proteins, spanning a range of organelles and subcellular structures in more than one
cell line, reported cross-linking as essential for work covering many proteins at once, so the
two routes are not interchangeable. What that comparison asks anyone to account for is how
accessible a protein is in the compartment it occupies, and the chemistry of the protein itself.

The preparation can also move the protein or take it away. Getting an antibody inside a cell
means the cell is dead and permeabilized before the antibody arrives, and introducing reagents
that way can extract a protein or relocalize it, so the picture need not reflect the living
cell. Nothing in the resulting image records that this has happened, which is why a
localization seen only in fixed cells is worth complementing with a method that watches living
ones.

A pattern in the expected place is the claim most exposed to the reader's own expectation. When a
large set of human proteins was localized both by immunofluorescence and by tagging the protein
genetically with a fluorescent partner, the two methods agreed for most of them, and the
discrepancies that remained were reported as systematic rather than random. The same work found
many proteins present in more than one compartment by both methods, so a single expected
location is a weaker prior than it feels.

What immunofluorescence establishes is where signal appeared in one fixed cell prepared one
way. Because nothing was separated by size before the antibody arrived, the image does not say
what molecular species produced the signal, and a related protein sitting in the same
compartment would look much the same. Because a fixed cell is not a living one, the image also
does not establish where the protein was before the fixative reached it.
