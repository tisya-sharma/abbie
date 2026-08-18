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
    depth: full-text
  - label: "Ayoubi R, et al. Scaling of an antibody validation procedure enables quantification of antibody performance in major research applications. eLife. 2023;12:RP91645."
    url: https://doi.org/10.7554/eLife.91645
    short: "Ayoubi 2023"
    journal: "eLife"
    title: "Scaling of an antibody validation procedure enables quantification of antibody performance in major research applications"
    depth: full-text
  - label: "Ayoubi R, Ryan J, Gonzalez Bolivar S, et al. A consensus platform for antibody characterization. Nat Protoc. 2025;20(6):1509-1545."
    url: https://doi.org/10.1038/s41596-024-01095-8
    short: "Ayoubi 2025"
    journal: "Nat Protoc"
    title: "A consensus platform for antibody characterization"
    depth: full-text
status: sourced
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
    proves: Residual signal is real cross-reactivity, not an incomplete knockout
  - item: No-primary control, everything except the primary antibody
    proves: The signal is not the detection system on its own
  - item: Loading control or total protein normalization
    proves: Compared lanes carried equivalent protein, so a lost band means something
  - item: Primary antibody titrated until the signal sits inside the linear range
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
skip: the knockout has to be confirmed in the protein and not only in the DNA, because a line
whose edit has been verified by genomic PCR and sequencing can still carry target protein,
sometimes as a truncated version of it. The line is screened with antibodies alongside its
parental line before it is trusted as a negative.

A no-primary control closes off the detection system itself. The sample receives everything
except the primary antibody, so anything that still appears cannot have come from the primary,
because none was there. A large characterization protocol reserves dedicated wells for exactly
this on every plate, one for each species of primary antibody in the run.

A loading control closes off the possibility that two lanes are not comparable. It is the
quietest control and the one whose absence does the most damage, because every claim of the form
"the signal disappeared" depends on the two samples having carried equivalent protein in the
first place.

Titration closes off the possibility that you simply used too much antibody. Insufficient
dilution of the primary, or an over-long incubation, promotes off-target binding and undesired
bands, so a reagent can look non-selective when the real finding is that it was never
optimized. What the titration aims at is the linear range of the assay: one characterization
protocol raises the concentration fivefold when nothing appears after a long exposure, and
lowers it fivefold when the signal is already saturated at the shortest one.

What no control does is transfer. A control set that establishes attribution in one application
and one sample type says nothing on its own about another.
