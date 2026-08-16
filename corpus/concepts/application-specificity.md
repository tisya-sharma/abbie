---
id: application-specificity
title: Why validation attaches to an application, not to an antibody
aliases:
  - what is an application
  - does validation transfer between applications
  - why does my antibody work in Western blot but not IF
  - is this antibody validated
ask: Does validation in one assay carry over to another?
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
  - label: "Ayoubi R, Ryan J, Gonzalez Bolivar S, et al. A consensus platform for antibody characterization. Nat Protoc. 2025;20(6):1509-1545."
    url: https://doi.org/10.1038/s41596-024-01095-8
    short: "Ayoubi 2025"
    journal: "Nat Protoc"
    title: "A consensus platform for antibody characterization"
  - label: "Ayoubi R, et al. Scaling of an antibody validation procedure enables quantification of antibody performance in major research applications. eLife. 2023;12:RP91645. Source for the direction-of-transfer finding."
    url: https://doi.org/10.7554/eLife.91645
    short: "Ayoubi 2023"
    journal: "eLife"
    title: "Scaling of an antibody validation procedure enables quantification of antibody performance in major research applications"
status: draft
reviewed_by:
clearance: public
level: core
requires:
  - antibody-validation
  - what-is-a-target
leads_to:
  - experimental-readout
  - genetic-perturbation-controls
  - species-cross-reactivity
---

An application is a specific experimental use of an antibody — Western blot, immunofluorescence,
immunohistochemistry, flow cytometry, enzyme-linked immunosorbent assay (ELISA),
immunoprecipitation. Antibodies are fit-for-purpose reagents, and validation attaches to the
application rather than to the antibody in general. "This antibody works" is an incomplete
sentence; it only means something as "this antibody works for this application, in this kind of
sample."

The reason is that different methods leave the protein in different physical states before the
antibody ever meets it. Proteins are typically in near-native form for flow cytometry and sandwich
assays, but wholly or partly denatured for Western blot, immunohistochemistry, and
immunocytochemistry. Because of differences in protein conformation and target accessibility,
antibodies that perform well in one context may perform inadequately in others. Fixation and
antigen retrieval add further changes to what remains recognizable.

Sample context matters as much as method. Validation data from one cell or tissue extract cannot
necessarily be used to prove equivalent performance in another cellular context, and even changing
a blocking buffer or detergent may alter performance. The number of similar proteins present also
varies between assay, cell type, and tissue, which changes how much opportunity there is for
off-target binding.

This is not theoretical. When 96 monoclonals selected for immunoreactivity in ELISA were tested in
Western blot, immunohistochemistry on brain sections, and immunofluorescence, the conclusion was
that antibodies may be suitable for one assay but unsuitable for another even highly related assay,
and that validation needs to be performed for each intended purpose.

Transfer is not uniformly zero in every direction — success in immunofluorescence has been reported
as the best predictor of performance in Western blot and immunoprecipitation — but the direction of
transfer cannot be assumed, and evidence in one application does not substitute for evidence in
another.
