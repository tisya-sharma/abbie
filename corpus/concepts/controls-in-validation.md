---
id: controls-in-validation
title: What each control proves
aliases:
  - controls
  - positive control
  - negative control
  - loading control
  - no-primary control
  - which controls do I need
ask: What does each validation control actually prove?
provenance: summarized
sources:
  - label: "Pillai-Kastoori L, Schutz-Geschwender AR, Harford JA. A systematic approach to quantitative Western blot analysis. Anal Biochem. 2020;593:113608."
    url: https://doi.org/10.1016/j.ab.2020.113608
    short: "Pillai-Kastoori 2020"
    journal: "Anal Biochem"
    title: "A systematic approach to quantitative Western blot analysis"
  - label: "Ayoubi R, et al. Scaling of an antibody validation procedure enables quantification of antibody performance in major research applications. eLife. 2023;12:RP91645."
    url: https://doi.org/10.7554/eLife.91645
    short: "Ayoubi 2023"
    journal: "eLife"
    title: "Scaling of an antibody validation procedure enables quantification of antibody performance in major research applications"
  - label: "Ayoubi R, Ryan J, Gonzalez Bolivar S, et al. A consensus platform for antibody characterization. Nat Protoc. 2025;20(6):1509-1545."
    url: https://doi.org/10.1038/s41596-024-01095-8
    short: "Ayoubi 2025"
    journal: "Nat Protoc"
    title: "A consensus platform for antibody characterization"
status: draft
reviewed_by:
clearance: public
level: core
requires:
  - antibody-validation
leads_to:
  - genetic-perturbation-controls
  - application-western-blot
# Rendered into the downloadable checklist, never into the model's context.
# Each item names the alternative explanation it closes off, because a control
# a reader cannot justify is a control they will drop under time pressure.
checklist:
  - item: Positive control expressing the target at endogenous level
    proves: The assay could have detected the target at all
  - item: Endogenous rather than overexpressed, and not a low expresser
    proves: Neither a false negative from too little nor masked off-target binding from too much
  - item: Negative genetic control, isogenic knockout or knockdown
    proves: The signal tracks the gene rather than something else
  - item: Knockout confirmed at the protein level, not only by genotype
    proves: Residual signal is real cross-reactivity, not a rescued frameshift
  - item: Knockdown removes at least half the target protein
    proves: The negative control is negative enough to interpret
  - item: No-primary lane, primary antibody omitted
    proves: The signal is not the detection system on its own
  - item: Loading control or total protein normalization
    proves: Compared lanes carried equivalent protein, so a lost band means something
  - item: Primary antibody titrated, reported as concentration not dilution
    proves: Extra bands are the reagent, not an over-concentrated primary
---

Every control answers one question, and it is always the same question asked about a different
suspect: what else could have produced this result? Controls are not a checklist bolted onto an
experiment. Each one closes off a specific alternative explanation, and knowing which
explanation each closes is what lets you tell a strong result from a lucky one.

A positive control closes off the possibility that the assay simply could not have worked. It is
a sample known to carry the target at a level the assay can detect, and the level matters in
both directions. Too little and a perfectly good antibody produces nothing, so the reagent gets
blamed for the sample: one large characterization program chose parental cell lines specifically
for expressing enough target to be seen by a binder in the single-digit to fifty nanomolar
range, screening candidate lines on measured RNA abundance before building anything. Too much is
the opposite trap, because overexpression gives the antibody an artificial advantage and can
hide off-target binding that would appear at natural levels. What you want is endogenous
expression that is comfortably detectable, which is not the same thing as low.

A negative control closes off the possibility that the signal came from something other than the
target, and the genetic version is the strongest form. It carries one condition that is easy to
skip: the knockout or knockdown has to be confirmed in the protein, not only in the DNA, and a
knockdown is generally expected to remove at least half the target protein before it can serve
as a negative control at all.

A no-primary lane closes off the detection system itself. Run the sample with the primary
antibody omitted, and anything that still appears is an artifact by definition, because there
was no primary antibody present to produce it.

A loading control closes off the possibility that two lanes are not comparable. It is the
quietest control and the one whose absence does the most damage, because every claim of the form
"the signal disappeared" depends on the two samples having carried equivalent protein in the
first place.

Titration closes off the possibility that you simply used too much antibody. Specificity depends
on concentration, and an over-concentrated primary generates off-target bands that vanish once
the concentration is optimized, so a reagent can look non-selective when the real finding is
that it was never titrated. Reporting the amount as a concentration rather than a dilution is
what makes that number mean anything to someone else.

What no control does is transfer. A control set that establishes attribution in one application
and one sample type says nothing on its own about another.
