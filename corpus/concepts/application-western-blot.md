---
id: application-western-blot
title: Western blot as an application
aliases:
  - western blot
  - WB
  - immunoblot
  - blotting
  - what does a blot show
ask: What does a Western blot actually establish?
provenance: summarized
sources:
  - label: "Pillai-Kastoori L, Schutz-Geschwender AR, Harford JA. A systematic approach to quantitative Western blot analysis. Anal Biochem. 2020;593:113608."
    url: https://doi.org/10.1016/j.ab.2020.113608
    short: "Pillai-Kastoori 2020"
    journal: "Anal Biochem"
    title: "A systematic approach to quantitative Western blot analysis"
  - label: "Ghosh R, Gilda JE, Gomes AV. The necessity of and strategies for improving confidence in the accuracy of western blots. Expert Rev Proteomics. 2014;11(5):549-560."
    url: https://doi.org/10.1586/14789450.2014.939635
    short: "Ghosh 2014"
    journal: "Expert Rev Proteomics"
    title: "The necessity of and strategies for improving confidence in the accuracy of western blots"
  - label: "Tsuji Y. Transmembrane protein western blotting: Impact of sample preparation on detection of SLC11A2 (DMT1) and SLC40A1 (ferroportin). PLoS One. 2020;15(7):e0235563."
    url: https://doi.org/10.1371/journal.pone.0235563
    short: "Tsuji 2020"
    journal: "PLoS One"
    title: "Transmembrane protein western blotting: Impact of sample preparation on detection of SLC11A2 (DMT1) and SLC40A1 (ferroportin)"
status: draft
reviewed_by:
clearance: public
level: core
requires:
  - application-specificity
leads_to:
  - controls-in-validation
  - selectivity
# Rendered into the downloadable checklist, never into the model's context.
# These are the blot-specific ways a result goes wrong before any control is
# read, which is why they sit ahead of the controls rather than beside them.
checklist:
  - item: Denaturation conditions chosen for the target
    proves: A multipass membrane protein has not aggregated in the well from boiling
  - item: Lysis buffer suited to where the protein lives
    proves: A blank lane is a real absence, not a failed extraction
  - item: Blocking agent matched to the target
    proves: Casein in milk is not competing with a phospho-specific antibody
  - item: Secondary checked against the sample species
    proves: Bands near 50 and 25 kDa are the target, not endogenous heavy and light chains
  - item: Signal inside the linear range, no saturation
    proves: Any comparison drawn across the band is quantitatively meaningful
  - item: Extra bands considered before being called nonspecific
    proves: Degradation, modification and splice variants have been ruled out first
---

A Western blot spreads the proteins in a sample out along a lane by size, moves them onto a
membrane, and asks an antibody to find one of them. Because the usual version denatures the
protein first, the antibody meets an unfolded chain rather than a folded shape, which is why
performance on a blot does not predict performance in an assay that keeps the protein intact.

The step most often treated as fixed is the one most worth examining: how the sample was
prepared. Denaturation conditions are a variable you control and can get wrong. Proteins that
cross the membrane several times aggregate when boiled, and the aggregates either smear or never
leave the well, so a target can vanish for reasons that have nothing to do with the antibody. In
a direct comparison on two transporters, unheated samples resolved cleanly while five minutes at
ninety-five degrees destroyed the resolution entirely.

Blocking is similarly invisible in the final image and can fail in both directions. Too much
blocking agent, or too long in it, can mask the interaction you are trying to see. In the other
direction, nonfat dry milk contains casein, which is itself phosphorylated, so milk used with a
phospho-specific antibody competes with the very signal being measured, and a defined protein
such as serum albumin is the usual substitute.

The detection system deserves its own suspicion. A secondary antibody raised against the same
species as the sample will find that species' own immunoglobulin, producing bands near fifty and
twenty-five kilodaltons from heavy and light chains. Many proteins of interest run in that same
region, so the artifact appears exactly where it is hardest to dismiss.

Reading the bands is where interpretation goes wrong in both directions. A single band at the
expected size is consistent with the target but does not establish it. Extra bands are not
automatically contamination either, since degradation products, post-translational
modifications, and splice variants all produce genuine additional bands from the intended
protein. Quantitative claims carry a further condition: a saturated band has no headroom left,
so any comparison drawn across it understates the difference it appears to show.
