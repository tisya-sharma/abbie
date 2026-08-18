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
    depth: full-text
  - label: "Schnell U, Dijk F, Sjollema KA, et al. Immunolabeling artifacts and the need for live-cell imaging. Nat Methods. 2012;9(2):152-158."
    url: https://doi.org/10.1038/nmeth.1855
    short: "Schnell 2012"
    journal: "Nat Methods"
    title: "Immunolabeling artifacts and the need for live-cell imaging"
    depth: full-text
  - label: "Stadler C, Rexhepaj E, Singan VR, et al. Immunofluorescence and fluorescent-protein tagging show high correlation for protein localization in mammalian cells. Nat Methods. 2013;10(4):315-323."
    url: https://doi.org/10.1038/nmeth.2377
    short: "Stadler 2013"
    journal: "Nat Methods"
    title: "Immunofluorescence and fluorescent-protein tagging show high correlation for protein localization in mammalian cells"
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
# These are the ways a stained image misleads before any control is read, and
# all of them are decided during sample preparation rather than at the scope.
checklist:
  - item: Fixation chemistry chosen for this target rather than inherited from the protocol
    proves: Cross-linking and alcohol dehydration were treated as different experiments, not defaults
  - item: Absent signal treated as possible epitope masking before it is treated as absent protein
    proves: A blank field is a real negative, not the fixative hiding the site
  - item: Permeabilization checked against extraction of a soluble target
    proves: The protein was still in the cell when the antibody arrived
  - item: Pattern reproduced in more than one cell line
    proves: The localization belongs to the protein rather than to one line's behavior
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
paraformaldehyde and then permeabilized with a detergent. Eighteen proteins across eleven
subcellular compartments were put through six protocols in three human cell lines, and
cross-linking followed by Triton X-100 was the only one that worked everywhere. That is a
recommendation for breadth rather than a verdict on the alternatives, because the alcohols held
the Golgi and endoplasmic reticulum well and gave the sharpest contrast on cytoskeletal fibers,
while extracting soluble cytoplasmic proteins and failing at the plasma membrane and the
mitochondria. The fixative is a decision about your target, not a default.

Breadth has a price, and it lands where nobody looks. Of five hundred and six proteins carried
into a later comparison, sixty produced no staining at all, and for thirty-seven of those the
transcript data said the target was expressed in the cell being imaged. The authors read that
subset as false negatives and give epitope masking by the cross-linking fixation itself as the
likely cause. The protocol chosen because it works for the most proteins is the same protocol
quietly removing some of them.

The preparation can also move the protein or take it away, and this can be watched directly.
Fluorescent protein spread through the cytoplasm survives paraformaldehyde on its own, then
leaves the cytoplasm when the gentlest routine detergent step is applied, in a cell where the
true location was never in doubt. Getting an antibody inside a cell requires that step, so the
image is made after the opportunity to lose the target has already passed, and nothing in the
image records it.

A pattern in the expected place is the claim most exposed to the reader's own expectation, and
the same antibody does not even agree with itself across cell lines. Proteins localized by
immunofluorescence in three different human lines were identically distributed in all three only
about half the time, with method and fixation held constant. Comparing across methods looks
better and is a weaker test than it appears: of the four hundred and forty-six proteins that
gave scorable staining, eighty-two percent shared at least one location with a genetically
tagged version, but the tagging was done live in different cell lines, and sharing one location
out of several counts as agreement.

What immunofluorescence establishes is where signal appeared in a cell that was killed and
opened before the antibody met it. The image reports a location rather than an identity, so a
relative sitting in the same compartment looks much the same. And the claim most readers
actually take from such an image, that the protein lives there in the working cell, is the one
the method is least able to support, because every step between the living cell and the
photograph is a step that could have moved it.
