---
id: genetic-perturbation-controls
title: Knockout and knockdown as validation evidence
aliases:
  - knockout control
  - CRISPR validation
  - knockdown
  - what is a KO control
provenance: summarized
sources:
  - label: "Uhlén M, Bandrowski A, Carr S, et al. A proposal for validation of antibodies. Nat Methods. 2016;13(10):823-827."
    url: https://doi.org/10.1038/nmeth.3995
  - label: "Ayoubi R, et al. Scaling of an antibody validation procedure enables quantification of antibody performance in major research applications. eLife. 2023;12:RP91645."
    url: https://doi.org/10.7554/eLife.91645
  - label: "Ayoubi R, Ryan J, Gonzalez Bolivar S, et al. A consensus platform for antibody characterization. Nat Protoc. 2025;20(6):1509-1545."
    url: https://doi.org/10.1038/s41596-024-01095-8
  - label: "Smits AH, et al. Biological plasticity rescues target activity in CRISPR knock outs. PMID 31659326."
    url: https://pubmed.ncbi.nlm.nih.gov/31659326/
status: draft
reviewed_by:
clearance: public
level: advanced
requires:
  - paralogs-and-isoforms
  - five-pillars-iwgav
leads_to:
  - selectivity
  - application-specificity
---

The cleanest way to test whether a signal came from the intended protein is to remove the protein
and look again. Genetic strategies do exactly that: the target's expression is eliminated or
reduced, usually with CRISPR-Cas9 knockout or RNA interference knockdown, and the experiment is
repeated. The reasoning, as the field's validation proposal states it, is that once the target's
levels are substantially reduced, whatever signal remains is pointing at something else.

These approaches are powerful because they establish a direct link between the gene, the target
protein, and what the antibody detects. The strongest form uses an **isogenic** pair — two cell
lines genetically identical except that one has the target gene deleted — so the only difference
between the two experiments is the protein in question.

The evidence categories are not equal in practice. In a large characterization program,
manufacturers most often relied on orthogonal strategies, accounting for 61% of antibodies
recommended for Western blot and 83% for immunofluorescence, against 30% and 7% respectively
characterized genetically. When antibodies validated orthogonally for immunofluorescence were
retested against knockout controls, only 38% showed the expected specificity. The same comparison
in Western blot was much closer, at 80% against 89%, so this is a strong argument for genetic
evidence in imaging specifically rather than a general indictment of orthogonal methods.

**Two limits.** Genetic strategies cannot be used for some sample types, in particular human
tissue samples and body fluids such as plasma and serum. And residual signal is not infallible
proof of cross-reactivity: knockouts can retain a truncated or internally deleted product, so a
knockout line's genotype needs verifying before residual signal is interpreted.
