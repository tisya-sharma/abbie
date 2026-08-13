---
id: why-validation-matters
title: Why antibody validation matters
aliases:
  - why bother validating
  - antibody reproducibility problem
  - why is validation important
  - what goes wrong without validation
ask: Why does antibody validation matter?
provenance: summarized
sources:
  - label: "Uhlén M, Bandrowski A, Carr S, et al. A proposal for validation of antibodies. Nat Methods. 2016;13(10):823-827."
    url: https://doi.org/10.1038/nmeth.3995
    short: "Uhlén 2016"
    journal: "Nat Methods"
    title: "A proposal for validation of antibodies"
  - label: "Taussig MJ, Fonseca C, Trimmer JS. Antibody validation: a view from the mountains. N Biotechnol. 2018;45:1-8."
    url: https://doi.org/10.1016/j.nbt.2018.08.002
    short: "Taussig 2018"
    journal: "N Biotechnol"
    title: "Antibody validation: a view from the mountains"
  - label: "Biddle et al. Improving the integrity and reproducibility of research that uses antibodies. mAbs. 2024;16(1):2323706."
    url: https://doi.org/10.1080/19420862.2024.2323706
    short: "Biddle 2024"
    journal: "mAbs"
    title: "Improving the integrity and reproducibility of research that uses antibodies: a technical, data sharing, behavioral and policy challenge"
status: draft
reviewed_by:
clearance: public
level: foundational
requires: []
leads_to:
  - antibody-validation
  - reagent-reproducibility
  - application-specificity
---

Antibodies are among the most widely used reagents in biology, and conclusions drawn with them
inherit whatever is true of the reagent. If an antibody binds something other than its intended
target, the experiment still produces a clean, publishable-looking result — it just means
something different from what the figure legend says. Nothing about the output signals the
problem, which is what makes this failure mode distinctive.

Reagent reliability has consequently become a recognized contributor to the wider reproducibility
problem in biomedical research, and it has been treated as such by the field for a decade. The
response has been a series of proposals for what validation should require, community initiatives
generating and publishing validation data at scale, and growing attention to how antibodies are
described in the literature so that a reader can tell which reagent was used at all.

The cost of skipping validation is asymmetric. Running the necessary controls is a bounded amount
of work, done once per application. Discovering afterward that a reagent was not selective can
invalidate a body of results built on it, and the discovery may come years later, from someone
else, after the conclusions have been cited.

The problem is also not solved by buying carefully. Two lots of the same catalog antibody may not
be the same molecule, and an antibody that performs well in one application frequently fails in
another, so neither a supplier's datasheet nor a colleague's success transfers automatically to a
new experiment. Both facts have practical consequences serious enough to be treated separately.

None of this makes antibodies unreliable tools. It makes them tools whose reliability is a
property of evidence rather than of reputation, and validation is the process that produces that
evidence.
