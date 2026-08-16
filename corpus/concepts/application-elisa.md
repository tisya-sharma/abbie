---
id: application-elisa
title: ELISA as an application
aliases:
  - ELISA
  - enzyme-linked immunosorbent assay
  - immunoassay
  - plate assay
  - sandwich assay
  - what does the plate reader show
ask: What does an ELISA actually establish?
provenance: summarized
sources:
  - label: "Butler JE. Solid supports in enzyme-linked immunosorbent assay and other solid-phase immunoassays. Methods. 2000;22(1):4-23."
    url: https://doi.org/10.1006/meth.2000.1031
    short: "Butler 2000"
    journal: "Methods"
    title: "Solid supports in enzyme-linked immunosorbent assay and other solid-phase immunoassays"
    depth: full-text
  - label: "Sturgeon CM, Viljoen A. Analytical error and interference in immunoassay: minimizing risk. Ann Clin Biochem. 2011;48(Pt 5):418-432."
    url: https://doi.org/10.1258/acb.2011.011073
    short: "Sturgeon 2011"
    journal: "Ann Clin Biochem"
    title: "Analytical error and interference in immunoassay: minimizing risk"
    depth: full-text
  - label: "Hoofnagle AN, Wener MH. The fundamental flaws of immunoassays and potential solutions using tandem mass spectrometry. J Immunol Methods. 2009;347(1-2):3-11."
    url: https://doi.org/10.1016/j.jim.2009.06.003
    short: "Hoofnagle 2009"
    journal: "J Immunol Methods"
    title: "The fundamental flaws of immunoassays and potential solutions using tandem mass spectrometry"
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
# The last item is the one that matters most, because the usual reassurance
# checks are the ones the interference literature says can pass while wrong.
checklist:
  - item: Coating treated as a step that alters the antigen, not only as immobilization
    proves: A weak signal was considered as denatured coat before it was called low abundance
  - item: Capture reagent chosen knowing it is itself adsorbed and partly denatured
    proves: The reagent was selected for surviving the surface, not only for affinity
  - item: Wells coated and blocked but given no sample
    proves: The color belongs to the target rather than to the plate or the substrate
  - item: The sample's own antibody content considered against the assay's antibodies
    proves: A high reading is the target and not a bridge formed across the two reagents
  - item: A dilution series run rather than one dilution, in a two-site format
    proves: A low reading is a low concentration and not a very high one saturating both reagents
  - item: Apparent linearity and recovery not treated as proof that interference is absent
    proves: The check that can pass while wrong has not been mistaken for a clearance
---

An ELISA gives you one number per well. Something bound to the bottom of the well captures the
target out of whatever was added, a second antibody carrying an enzyme finds it, the enzyme
turns a colorless solution a color, and a reader measures how much color there is. No image, no
band, no lane. A number.

The plastic is a participant rather than a container, and this is the fact the method is usually
taught without. Adsorbing a protein onto a hydrophobic polymer such as polystyrene has been
described as a denaturation event not unlike treating it with a strong chaotropic salt, and most
adsorbed protein ends up partly or largely denatured. Coating a plate is therefore something
done to the antigen, and it can lose an epitope outright, bury one against the surface, or leave
one recognizable but at much lower affinity.

Adsorption is efficient as adhesion and poor as preservation, and conflating the two is the
common error. Somewhere between half and four fifths of most protein antigens adsorb stably when
conditions are optimized, which sounds reassuring until you notice it describes how much
material stays on the plate rather than how much of it still works.

This is why the sandwich format exists, and it is worth being precise about what it does. Using
a capture antibody rather than coating the target directly keeps the target off the plastic
entirely, so the thing you are measuring stays close to its native form. That is the version of
the assay used for complex samples, and it is why a plate can be a near-native context for an
antigen even though the surface is not.

The cost moves rather than disappearing. The capture antibody is now what is stuck to the
plastic, only a small minority of it may survive there in working order, and the amount of
antigen a plate holds that way falls below what direct adsorption achieves. Polyclonal capture
reagents tend to outlast monoclonal ones, because a single clone that does not survive
adsorption fails uniformly while a mixed population is unlikely to fail all at once.

Because the readout carries no structure, nothing in a result announces that it has gone wrong.
Antibodies already present in a sample can bridge the capture and detection reagents and drive
the reading up whether or not any target is bound, and the same antibodies can block one side
and drive it down. In formats where both reagents meet the sample at once, a very high
concentration can saturate them separately so that no sandwich forms and the reading falls
instead of rising. The reassurance checks are weaker than their reputation, since acceptable
dilution behavior and recovery can both be observed while an interfering substance is present.

What an ELISA establishes is how much color one well produced under one set of conditions.
Nothing was separated before the antibody arrived, so the number carries no information about
the size or the identity of what was bound, and confirming what a signal is made of calls for a
method that identifies the molecule rather than detecting an epitope.
