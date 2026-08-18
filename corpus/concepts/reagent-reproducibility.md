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
  - label: "Bradbury ARM, Trinklein ND, Thie H, et al. When monoclonal antibodies are not monospecific: Hybridomas frequently express additional functional variable regions. mAbs. 2018;10(4):539-546."
    url: https://doi.org/10.1080/19420862.2018.1445456
    short: "Bradbury 2018"
    journal: "mAbs"
    title: "When monoclonal antibodies are not monospecific: Hybridomas frequently express additional functional variable regions"
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
  - label: "Uhlén M, Bandrowski A, Carr S, et al. A proposal for validation of antibodies. Nat Methods. 2016;13(10):823-827. Source for sequenced reagents being recreatable in perpetuity while sequence knowledge stays independent of specificity, which is this concept's closing claim."
    url: https://doi.org/10.1038/nmeth.3995
    short: "Uhlén 2016"
    journal: "Nat Methods"
    title: "A proposal for validation of antibodies"
    depth: full-text
  - label: "Bradbury A, Plückthun A. Reproducibility: standardize antibodies used in research. Nature. 2015;518(7537):27-29. Source for the case that sequence-defined recombinant reagents are what make an antibody reproducible. A different paper from Bradbury 2018 above."
    url: https://doi.org/10.1038/518027a
    short: "Bradbury 2015"
    journal: "Nature"
    title: "Reproducibility: Standardize antibodies used in research"
    depth: full-text
  - label: "Freedman LP. Antibodies: validate recombinants too. Nature. 2015;518(7540):483. Source for recombinant antibodies still needing functional validation despite their minimal batch-to-batch variability."
    url: https://doi.org/10.1038/518483c
    short: "Freedman 2015"
    journal: "Nature"
    title: "Antibodies: Validate recombinants too"
    depth: full-text
status: sourced
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

A polyclonal antibody is a mixture harvested from an immunized animal, and the mixture is never
quite the same twice. Immunizing an animal, even the same animal again, never results in exactly
the same set of antibodies, so functionality varies from batch to batch and the specificity of any
one batch is hard to be sure of. Serum is also a finite supply, so once one is exhausted the
replacement comes from a different animal and differs again. A monoclonal antibody from a
hybridoma is intended to be a single uniform molecule, but hybridoma cell lines can acquire
rearrangements and mutations over time, particularly after prolonged culture. Lot numbers matter
for both reasons.

Hybridomas are also less uniform than the name suggests. In a multicenter set of 185 hybridomas
drawn from seven laboratories over roughly twenty years, assembled without preselection for
problem cases though about 90% came from three commercial suppliers, 126 (68.1%) contained no
additional productive antibody chains while the remaining 59 (31.9%) expressed one or more extra
productive heavy or light chain V genes. That prevalence was read from the antibody transcripts,
and the same study's functional comparisons do not isolate the extra chains as the cause:
recombinant versions bound more strongly and more selectively than antibody purified from the
parent hybridoma supernatant, but so did the recombinant versions of hybridomas in which only one
heavy and one light chain were found.

A recombinant antibody is produced from a known DNA sequence, so the same sequence yields the
same protein indefinitely. In a head-to-head comparison of 614 commercial antibodies against 65
human protein targets, recombinants outperformed both other formats in Western blot: 67% of the
191 recombinants immunodetected their target, against 41% of 165 monoclonals and 27% of 258
polyclonals. The authors note the advantage may be correlational, since recombinants are newer
reagents that may have had more characterization from their suppliers, and the antibodies tested
were chosen from the participating manufacturers' own catalogs by those manufacturers, who gave
recombinants the highest priority.

Sequence definition fixes identity, not performance. Fully sequenced reagents can be
identified unambiguously and recreated in perpetuity, but sequence knowledge is independent of
specificity and does not remove the need for validation. A perfectly reproducible antibody can be
reproducibly wrong.
