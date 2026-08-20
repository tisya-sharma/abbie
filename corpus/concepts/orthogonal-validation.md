---
id: orthogonal-validation
title: Orthogonal validation
aliases:
  - orthogonal strategy
  - independent method validation
  - antibody-independent evidence
  - how do I know the signal is real
ask: What is orthogonal validation?
provenance: summarized
sources:
  - label: "Uhlén M, Bandrowski A, Carr S, et al. A proposal for validation of antibodies. Nat Methods. 2016;13(10):823-827."
    url: https://doi.org/10.1038/nmeth.3995
    short: "Uhlén 2016"
    journal: "Nat Methods"
    title: "A proposal for validation of antibodies"
    depth: full-text
  - label: "Ayoubi R, Ryan J, Gonzalez Bolivar S, et al. A consensus platform for antibody characterization. Nat Protoc. 2025;20(6):1509-1545."
    url: https://doi.org/10.1038/s41596-024-01095-8
    short: "Ayoubi 2025"
    journal: "Nat Protoc"
    title: "A consensus platform for antibody characterization"
    depth: full-text
  - label: "Edfors F, Hober A, Linderbäck K, et al. Enhanced validation of antibodies for research applications. Nat Commun. 2018;9:4130. Source for orthogonal validation run at scale against independent measurement."
    url: https://doi.org/10.1038/s41467-018-06642-y
    short: "Edfors 2018"
    journal: "Nat Commun"
    title: "Enhanced validation of antibodies for research applications"
    depth: full-text
  - label: IPI 4D framework, internal draft. Grounds the statements of IPI's own position. No manuscript text is reproduced.
    depth: full-text
status: sourced
reviewed_by:
clearance: public
level: advanced
requires:
  - selectivity
leads_to:
  - genetic-perturbation-controls
  - evidence-strengthening-approaches
  - interpretive-principles
---

Orthogonal validation compares what an antibody reports against a measurement of the same protein
made without using that antibody. If antibody signal tracks an independent estimate of abundance
across samples where the protein genuinely varies, the signal is behaving as the target should.
If it does not track, something is wrong with the attribution.

The independence is the whole point. Two antibodies from the same immunization, or the same
antibody in two applications, share whatever assumption is failing. A method that does not
involve antibodies at all, such as a mass-spectrometry-based measure of protein abundance or
transcript-level expression data used with appropriate caution, fails differently, so agreement
between the two is genuinely informative rather than a repeated measurement of the same
potential error.

Its natural use is **selectivity**. Establishing that an antibody binds its target is comparatively
easy; establishing that observed signal comes from that target rather than a relative is the
harder problem, and correlating signal against an antibody-independent measurement across a panel
of samples is one of the few ways to attack it without genetic perturbation.

The caveats are real. Reading protein abundance from transcript levels rests on the assumption
that messenger RNA and protein track one another at steady state, and the comparison needs
samples where the protein genuinely varies. In the program that ran this at scale, antibodies
that fell below the correlation cutoff only because their target barely differed across the
panel were then confirmed as specific by the proteomics comparison and by knockdown, so a failed
correlation can be a verdict on the panel rather than on the antibody. Nothing the transcript
comparison passed was later contradicted, which is the reassuring half of the same result.

In IPI's framework this is an evidence-strengthening approach rather than a dimension. It
produces no new claim by itself; it changes how much confidence a result generated elsewhere
deserves.
