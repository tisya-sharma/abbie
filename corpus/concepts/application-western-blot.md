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
    depth: full-text
  - label: "Ghosh R, Gilda JE, Gomes AV. The necessity of and strategies for improving confidence in the accuracy of western blots. Expert Rev Proteomics. 2014;11(5):549-560."
    url: https://doi.org/10.1586/14789450.2014.939635
    short: "Ghosh 2014"
    journal: "Expert Rev Proteomics"
    title: "The necessity of and strategies for improving confidence in the accuracy of western blots"
    depth: full-text
  - label: "Tsuji Y. Transmembrane protein western blotting: Impact of sample preparation on detection of SLC11A2 (DMT1) and SLC40A1 (ferroportin). PLoS One. 2020;15(7):e0235563."
    url: https://doi.org/10.1371/journal.pone.0235563
    short: "Tsuji 2020"
    journal: "PLoS One"
    title: "Transmembrane protein western blotting: Impact of sample preparation on detection of SLC11A2 (DMT1) and SLC40A1 (ferroportin)"
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
# These are the blot-specific ways a result goes wrong before any control is
# read, which is why they sit ahead of the controls rather than beside them.
checklist:
  - item: Heating conditions chosen for this target rather than inherited from the protocol
    proves: A missing band is a real absence, not a protein left stuck at the top of the gel
  - item: Lysis buffer suited to where the protein lives
    proves: A blank lane is a real absence, not a failed extraction
  - item: Blocking agent matched to the target
    proves: Casein in milk is not being detected by a phospho-specific antibody
  - item: Detection chemistry considered when a band looks unusually strong or hollow
    proves: Reverse banding is substrate depletion, not a feature of the sample
  - item: Signal inside the linear range, no saturation
    proves: Any comparison drawn across the band is quantitatively meaningful
  - item: Extra bands considered before being called nonspecific
    proves: Degradation, modification and splice variants have been ruled out first
---

A Western blot spreads the proteins in a sample out along a lane by size, moves them onto a
membrane, and asks an antibody to find one of them. The standard preparation denatures the
protein first, heating it in a buffer carrying a detergent and a reducing agent, so the antibody
meets an unfolded chain fixed to a membrane rather than a folded shape in solution, and one
recognized way for a blot to fail is that the antibody does not recognize its antigen in that
state.

The step most often treated as fixed is the one most worth examining: how the sample was
prepared. Heating is a variable you control, and it can be wrong in either direction. Five
minutes at ninety-five degrees ruined the blot for one transporter that crosses the membrane
twelve times, leaving its protein stuck at the top of the separating gel, while unheated
samples of the same lysate resolved it cleanly. The same treatment only partly impaired a
second twelve-pass transporter, and the authors say plainly that they have no good explanation
for why the two behaved differently. Heating runs the other way for some proteins: a cytoplasmic
storage protein assembled from twenty-four subunits could be detected only in heated samples,
because unheated it gave no band at all or failed to enter the gel. There is no default that is
safe for every target.

Blocking is similarly invisible in the final image and can fail in both directions. Too little
blocking, or too short a time in it, leaves nonspecific bands, while overblocking weakens the
signal from the target itself. The failure that catches people out is more specific than either:
a phospho-specific antibody can recognize the casein in nonfat dry milk, so the blocking agent
becomes a source of background rather than a defense against it. The remedy is to determine the
blocking reagent and the incubation time for each new antibody rather than inheriting them, and
a blocked scrap of membrane taken through the primary and secondary alone will show whether the
blocker is what is producing the background.

The detection chemistry deserves its own suspicion, because it is not a neutral window onto the
blot. In the common enzymatic scheme the signal depends on how fast an enzyme consumes its
substrate, and that rate varies across the surface of the membrane and over time. Where the
enzyme is concentrated the substrate is used up quickly, which produces the hollow reverse bands
and the burned-in patches a reader would otherwise take for features of the sample. Fluorescent
detection does not depend on substrate availability or timing, which is why it is what the
systematic quantitative protocols recommend.

Reading the bands is where interpretation goes wrong in both directions. A single band at the
expected size is consistent with the target but does not establish it. Extra bands are not
automatically contamination either, since degradation products, post-translational
modifications, and splice variants all produce genuine additional bands from the intended
protein. Quantitative claims carry a further condition: a saturated band has no headroom left,
so any comparison drawn across it understates the difference it appears to show.
