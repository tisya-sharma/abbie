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
  - label: "Baker M. 1,500 scientists lift the lid on reproducibility. Nature. 2016;533(7604):452-454. Source for the wider reproducibility problem this concept places reagents inside. A news feature reporting a survey, not primary research."
    url: https://doi.org/10.1038/533452a
    short: "Baker 2016"
    journal: "Nature"
    title: "1,500 scientists lift the lid on reproducibility"
  - label: "Bordeaux J, Welsh AW, Agarwal S, et al. Antibody validation. BioTechniques. 2010;48(3):197-209. Source for what validation evidence conventionally consists of, and for specificity, sensitivity and reproducibility as the field's framing."
    url: https://doi.org/10.2144/000113382
    short: "Bordeaux 2010"
    journal: "BioTechniques"
    title: "Antibody validation"
  - label: "Polakiewicz RD. Antibodies: the solution is validation. Nature. 2015;518(7540):483. Source for reliability resting on evidence rather than on reputation."
    url: https://doi.org/10.1038/518483b
    short: "Polakiewicz 2015"
    journal: "Nature"
    title: "Antibodies: The solution is validation"
  - label: IPI 4D framework, internal draft — defines the dimensions this concept names. No manuscript text is reproduced.
status: draft
reviewed_by:
clearance: public
level: foundational
requires: []
leads_to:
  - antibody-validation
  - reagent-reproducibility
  - application-specificity
  - what-is-an-antibody
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

The field's own long-standing framing asks for three things. Specificity is whether the signal
comes from the intended target rather than from something else. Sensitivity is whether the
antibody detects the target at the abundance the experiment will actually encounter.
Reproducibility is whether the same reagent gives the same result across lots and across days.
That framing is the field's rather than IPI's, and it is worth knowing because most published
guidance is written in it. IPI organizes the same evidence differently, into four dimensions.

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
