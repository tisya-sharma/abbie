---
id: reagent-reproducibility
title: Why the same antibody may not be the same antibody
aliases:
  - lot to lot variation
  - polyclonal vs monoclonal vs recombinant
  - why does my antibody stop working
  - what is a hybridoma
ask: Why can two lots of the same antibody behave differently?
provenance: summarized
sources:
  - label: "Bradbury ARM, et al. When monoclonal antibodies are not monospecific: hybridomas frequently express additional functional variable regions. mAbs. 2018;10(4):539-546."
    url: https://doi.org/10.1080/19420862.2018.1445456
    short: "Bradbury 2018"
    journal: "mAbs"
    title: "When monoclonal antibodies are not monospecific: hybridomas frequently express additional functional variable regions"
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
  - label: "Uhlén M, Bandrowski A, Carr S, et al. A proposal for validation of antibodies. Nat Methods. 2016;13(10):823-827."
    url: https://doi.org/10.1038/nmeth.3995
    short: "Uhlén 2016"
    journal: "Nat Methods"
    title: "A proposal for validation of antibodies"
  - label: "Bradbury A, Plückthun A. Reproducibility: standardize antibodies used in research. Nature. 2015;518(7537):27-29. Source for the case that sequence-defined recombinant reagents are what make an antibody reproducible. A different paper from Bradbury 2018 above."
    url: https://doi.org/10.1038/518027a
    short: "Bradbury 2015"
    journal: "Nature"
    title: "Reproducibility: Standardize antibodies used in research"
  - label: "Freedman LP. Antibodies: validate recombinants too. Nature. 2015;518(7540):483. Source for sequence definition fixing identity but not performance, which is this concept's closing claim."
    url: https://doi.org/10.1038/518483c
    short: "Freedman 2015"
    journal: "Nature"
    title: "Antibodies: Validate recombinants too"
status: draft
reviewed_by:
clearance: public
level: foundational
requires: []
leads_to:
  - molecular-integrity
  - what-is-binding
---

Buying the same catalog antibody twice does not guarantee receiving the same molecule twice, and
the reason depends on how the antibody was made.

A polyclonal antibody is a mixture harvested from an immunized animal. It is a finite
resource: when that supply is exhausted, the replacement comes from a different animal and is a
different mixture. A monoclonal antibody from a hybridoma is intended to be a single
uniform molecule, but hybridoma cell lines can undergo genetic drift over time in culture. Lot
numbers matter for both reasons.

Hybridomas are also less uniform than the name suggests. In a multicenter set of 185 hybridomas
drawn from seven laboratories over roughly twenty years — assembled without preselection for
problem cases, though about 90% came from three commercial suppliers — 126 (68.1%) contained no
additional productive antibody chains while the remaining 59 (31.9%) expressed one or more extra
productive heavy or light chain V genes. Note this was measured principally at the transcript
level, and the separate question of whether those extra chains degrade performance is not
established.

A recombinant antibody is produced from a known DNA sequence, so the same sequence yields the
same protein indefinitely. In a head-to-head comparison across a large antibody set, recombinants
outperformed both other formats in Western blot: 67% of recombinants immunodetected their target,
against 41% of monoclonals and 27% of polyclonals. The authors note this advantage is
correlational — recombinants are newer reagents and may have received more characterization from
suppliers — and several hold commercial interests in recombinant technology.

Sequence definition fixes identity, not performance. Fully sequenced reagents can be
identified unambiguously and recreated in perpetuity, but sequence knowledge is independent of
specificity and does not remove the need for validation. A perfectly reproducible antibody can be
reproducibly wrong.
