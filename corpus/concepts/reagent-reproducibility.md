---
id: reagent-reproducibility
title: Why the same antibody may not be the same antibody
aliases:
  - lot to lot variation
  - polyclonal vs monoclonal vs recombinant
  - why does my antibody stop working
  - what is a hybridoma
provenance: summarized
sources:
  - label: "Bradbury ARM, et al. When monoclonal antibodies are not monospecific: hybridomas frequently express additional functional variable regions. mAbs. 2018;10(4):539-546."
    url: https://doi.org/10.1080/19420862.2018.1445456
  - label: "Ayoubi R, et al. Scaling of an antibody validation procedure enables quantification of antibody performance in major research applications. eLife. 2023;12:RP91645."
    url: https://doi.org/10.7554/eLife.91645
  - label: "Ayoubi R, Ryan J, Gonzalez Bolivar S, et al. A consensus platform for antibody characterization. Nat Protoc. 2025;20(6):1509-1545."
    url: https://doi.org/10.1038/s41596-024-01095-8
  - label: "Uhlén M, Bandrowski A, Carr S, et al. A proposal for validation of antibodies. Nat Methods. 2016;13(10):823-827."
    url: https://doi.org/10.1038/nmeth.3995
status: draft
reviewed_by:
clearance: public
level: foundational
requires: []
leads_to:
  - molecular-integrity
  - what-is-binding
  - five-pillars-iwgav
---

Buying the same catalog antibody twice does not guarantee receiving the same molecule twice, and
the reason depends on how the antibody was made.

A **polyclonal** antibody is a mixture harvested from an immunized animal. It is a finite
resource: when that supply is exhausted, the replacement comes from a different animal and is a
different mixture. A **monoclonal** antibody from a **hybridoma** is intended to be a single
uniform molecule, but hybridoma cell lines can undergo genetic drift over time in culture. Lot
numbers matter for both reasons.

Hybridomas are also less uniform than the name suggests. In a multicenter set of 185 hybridomas
drawn from seven laboratories over roughly twenty years — assembled without preselection for
problem cases, though about 90% came from three commercial suppliers — 126 (68.1%) contained no
additional productive antibody chains while the remaining 59 (31.9%) expressed one or more extra
productive heavy or light chain V genes. Note this was measured principally at the transcript
level, and the separate question of whether those extra chains degrade performance is not
established.

A **recombinant** antibody is produced from a known DNA sequence, so the same sequence yields the
same protein indefinitely. In a head-to-head comparison across a large antibody set, recombinants
outperformed both other formats in Western blot: 67% of recombinants immunodetected their target,
against 41% of monoclonals and 27% of polyclonals. The authors note this advantage is
correlational — recombinants are newer reagents and may have received more characterization from
suppliers — and several hold commercial interests in recombinant technology.

**Sequence definition fixes identity, not performance.** Fully sequenced reagents can be
identified unambiguously and recreated in perpetuity, but sequence knowledge is independent of
specificity and does not remove the need for validation. A perfectly reproducible antibody can be
reproducibly wrong.
