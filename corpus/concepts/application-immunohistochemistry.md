---
id: application-immunohistochemistry
title: Immunohistochemistry as an application
aliases:
  - immunohistochemistry
  - IHC
  - tissue staining
  - stained section
  - antigen retrieval
  - what does the stain show
ask: What does immunohistochemistry actually establish?
provenance: summarized
sources:
  - label: "Shi SR, Shi Y, Taylor CR. Antigen retrieval immunohistochemistry: review and future prospects in research and diagnosis over two decades. J Histochem Cytochem. 2011;59(1):13-32."
    url: https://doi.org/10.1369/jhc.2010.957191
    short: "Shi 2011"
    journal: "J Histochem Cytochem"
    title: "Antigen retrieval immunohistochemistry: review and future prospects in research and diagnosis over two decades"
    depth: full-text
  - label: "Howat WJ, Lewis A, Jones P, et al. Antibody validation of immunohistochemistry for biomarker discovery: recommendations of a consortium of academic and pharmaceutical based histopathology researchers. Methods. 2014;70(1):34-38."
    url: https://doi.org/10.1016/j.ymeth.2014.01.018
    short: "Howat 2014"
    journal: "Methods"
    title: "Antibody validation of immunohistochemistry for biomarker discovery: recommendations of a consortium of academic and pharmaceutical based histopathology researchers"
    depth: full-text
  - label: "Hewitt SM, Baskin DG, Frevert CW, et al. Controls for immunohistochemistry: the Histochemical Society's standards of practice for validation of immunohistochemical assays. J Histochem Cytochem. 2014;62(10):693-697."
    url: https://doi.org/10.1369/0022155414545224
    short: "Hewitt 2014"
    journal: "J Histochem Cytochem"
    title: "Controls for immunohistochemistry: the Histochemical Society's standards of practice for validation of immunohistochemical assays"
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
# Most of these are decided before the section reaches the bench, which is why
# they sit ahead of the controls rather than beside them.
checklist:
  - item: Delay before fixative and duration in fixative known for the block
    proves: A weak stain is the antibody's doing rather than the sample's unrecorded history
  - item: Retrieval buffer, pH and heating recorded alongside the result
    proves: The condition that decided what was detectable can be repeated
  - item: Tissue known to carry the target run in the same batch
    proves: The run worked, so an absent stain means something
  - item: Negative control that substitutes matched immunoglobulin rather than omitting the primary
    proves: Background was tested against the primary's own class, not only the detection system
  - item: Tissue lacking the gene used wherever the target can be deleted
    proves: The stain tracks the gene rather than the reagent
  - item: An unexpected pattern treated as suspected nonspecific binding before it is treated as a finding
    proves: The likelier explanation was ruled out before the interesting one was accepted
---

A block of tissue reaches the bench having already been through a great deal. It was cut from a
body, left for some period before it went into fixative, held in formalin for however long the
routine allowed, then dehydrated, soaked in wax, and sliced thinner than a cell. Only after all
of that does an antibody get to look for anything in it.

Formalin preserves tissue by cross-linking proteins to one another, and the same chemistry is
what hides the target. The distinction matters for what can be recovered. Peptide epitopes
exposed to formalin on their own largely kept their immunoreactivity, and lost it when an
unrelated protein was present to be cross-linked to, which suggests the epitope is usually
masked by its neighbors rather than destroyed.

Antigen retrieval is the attempt to undo that, and it behaves like a setting rather than a step.
Heating is the mechanism most investigators credit with breaking the cross-links, and the pH and
ionic strength of the retrieval solution are described as critical to how well it works, which
is why validation protocols routinely compare two buffers at different pH. How much of the
protein any of this actually restores remains unknown.

Much of what determined the outcome happened before the sample arrived and was never written
down. The influence of fixation strength and duration on whether an epitope stays available has
been described as unknown and often unpredictable, and time spent without blood supply before
fixation can sharply reduce how much target is left to find. This variability is the reason
formalin fixation gets called a major uncontrollable factor in the method.

The expected pattern is the weakest evidence a stained section offers. A result departing from
what was predicted more often reflects the antibody binding something else than an interesting
observation, so the prediction cannot be what confirms the stain. Controls are what make the
section interpretable at all, and one common candidate does not count: omitting the primary
antibody tests whether the detection system stains on its own, and says nothing about whether
the primary bound what it was meant to. Substituting matched immunoglobulin tests that, and
tissue in which the gene has been deleted tests it best.

What immunohistochemistry establishes is that signal appeared in particular cells of one section
prepared one way. Because nothing was separated by size or charge before the antibody arrived,
neither a positive nor a negative result identifies the molecule that was stained, and the
method has no standard against which an amount could be read off.
