---
id: application-immunoprecipitation
title: Immunoprecipitation as an application
aliases:
  - immunoprecipitation
  - IP
  - co-immunoprecipitation
  - co-IP
  - pull-down
  - what does the pull-down show
ask: What does immunoprecipitation actually establish?
provenance: summarized
sources:
  - label: "Trinkle-Mulcahy L, Boulon S, Lam YW, et al. Identifying specific protein interaction partners using quantitative mass spectrometry and bead proteomes. J Cell Biol. 2008;183(2):223-239."
    url: https://doi.org/10.1083/jcb.200805092
    short: "Trinkle-Mulcahy 2008"
    journal: "J Cell Biol"
    title: "Identifying specific protein interaction partners using quantitative mass spectrometry and bead proteomes"
    depth: full-text
  - label: "Mellacheruvu D, Wright Z, Couzens AL, et al. The CRAPome: a contaminant repository for affinity purification-mass spectrometry data. Nat Methods. 2013;10(8):730-736."
    url: https://doi.org/10.1038/nmeth.2557
    short: "Mellacheruvu 2013"
    journal: "Nat Methods"
    title: "The CRAPome: a contaminant repository for affinity purification-mass spectrometry data"
    depth: full-text
  - label: "Marcon E, Jain H, Bhattacharya A, et al. Assessment of a method to characterize antibody selectivity and specificity for use in immunoprecipitation. Nat Methods. 2015;12(8):725-731."
    url: https://doi.org/10.1038/nmeth.3472
    short: "Marcon 2015"
    journal: "Nat Methods"
    title: "Assessment of a method to characterize antibody selectivity and specificity for use in immunoprecipitation"
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
# The items span controls, support, depletion, washing, and the readout.
checklist:
  - item: Control pull-down run with a matched irrelevant reagent on the same lysate and the same support
    proves: What came down is the antibody's doing rather than the support's
  - item: More than one negative control run rather than a single one
    proves: The background was characterized rather than sampled once
  - item: Support and buffer chosen knowing background differs between them and between fractions
    proves: The bead was treated as a variable rather than a constant
  - item: Depletion of the target from the extract measured rather than assumed
    proves: How efficiently the antibody isolated the target is known, which is what detecting its partners depends on
  - item: Wash stringency chosen against the claim being made, not maximized
    proves: A weakly bound real partner was not washed away in pursuit of a clean lane
  - item: The readout method's own controls run alongside the pull-down's
    proves: The second experiment's failure modes are not being read as the first one's result
---

An immunoprecipitation tells you nothing by itself. An antibody is mixed into a cell lysate,
given something solid to hold onto, and everything not stuck to it is washed away. What remains
is a small amount of material in a tube. To find out what is in it, you have to run a different
experiment, and that is the whole difficulty of the application: every conclusion is borrowed
from the method that comes next, and arrives dressed as that method's result.

The tube is also more crowded than a clean protocol suggests. An immunoprecipitate holds many
proteins besides the target before any background is removed, so the work of deciding what the
pull-down caught happens almost entirely after the bench step is finished.

Much of what is in the tube was never the antibody's doing. Affinity matrices are themselves a
major source of nonspecific binding for protein interaction work, and no single support suits
every application, with background differing between bead chemistries and between the cell
fractions they are used on. Across a large collection of negative-control purifications, a small
group of proteins appeared in more than nine experiments in ten, and a larger group in more than
half, which is why a background list is built from many controls rather than from one.

Washing harder is not the answer, and this is the counterintuitive part. Nonspecific binding
cannot be dealt with satisfactorily by raising stringency, and stringent purification loses real
partners, particularly those present in low amounts or binding weakly. The choice of wash
conditions is therefore a decision about which errors to accept rather than a dial toward
cleanliness.

What a pull-down asks of an antibody is also its own question. Antibodies raised to bind a
well-folded domain can serve here and still fail to detect the same protein once it is
denatured, so success in this application does not imply the reagent reads a blot. It does not
follow that pull-down evidence is useful nowhere else: in at least one large panel, reagents
that performed well here were frequently useful for imaging too, which is a different
application rather than a general licence.

What an immunoprecipitation establishes is that some material was retained by an antibody from
one lysate under one set of wash conditions. Whether the intended protein is in it, and whether
the antibody is why, belong to the method you run next and to the control pull-down you run
beside it. A second protein appearing alongside the target is a further and weaker claim again,
since the conditions that preserved it are the same ones deciding what survived to be caught.
