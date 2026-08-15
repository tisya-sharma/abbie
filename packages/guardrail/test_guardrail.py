"""Unit tests for the output guardrail. Run without an API key:

    python3 -m unittest packages.guardrail.test_guardrail
"""

import unittest

from packages.guardrail import (
    StreamScrubber,
    is_publishable,
    leak_scan,
    scrub_text,
)

SLUGS = {
    "antibody-validation",
    "five-pillars-iwgav",
    "molecular-integrity",
    "selectivity",
    "what-is-binding",
}


class ScrubTextTests(unittest.TestCase):
    def test_single_marker_removed_with_preceding_space(self):
        self.assertEqual(
            scrub_text("Integrity comes first [molecular-integrity]."),
            "Integrity comes first.",
        )

    def test_multi_id_semicolon_group_removed(self):
        self.assertEqual(
            scrub_text("Both matter [molecular-integrity; what-is-binding]."),
            "Both matter.",
        )

    def test_comma_and_space_group_removed(self):
        self.assertEqual(
            scrub_text("next? [molecular-integrity, what-is-binding, five-pillars-iwgav]"),
            "next?",
        )

    def test_title_form_group_removed(self):
        self.assertEqual(scrub_text("as shown [Molecular Integrity]."), "as shown.")

    def test_mid_sentence_group_leaves_single_space(self):
        self.assertEqual(
            scrub_text("purity [molecular-integrity] and binding"),
            "purity and binding",
        )

    def test_literal_bracket_content_preserved(self):
        text = "the buffer [pH 7.4!] stays"
        self.assertEqual(scrub_text(text), text)

    def test_unmatched_bracket_preserved(self):
        text = "an array[0 without close"
        self.assertEqual(scrub_text(text), text)

    def test_oversized_group_treated_as_prose(self):
        text = "[" + "a" * 400 + "]"
        self.assertEqual(scrub_text(text), text)

    def test_observed_five_slug_leak_removed(self):
        text = (
            "partly attributable to production."
            " [four-dimensional-framework; molecular-integrity;"
            " target-engagement; selectivity; application-specificity]"
        )
        self.assertEqual(scrub_text(text), "partly attributable to production.")

    def test_question_still_ends_with_question_mark(self):
        scrubbed = scrub_text("Want to go deeper? [antibody-validation]")
        self.assertTrue(scrubbed.endswith("?"))


class StreamScrubberTests(unittest.TestCase):
    def collect(self, chunks):
        scrubber = StreamScrubber()
        parts = [scrubber.feed(chunk) for chunk in chunks]
        parts.append(scrubber.flush())
        return "".join(parts)

    def test_marker_split_across_chunks(self):
        out = self.collect(["binding matters ", "[what-is-", "binding]", " a lot"])
        self.assertEqual(out, "binding matters a lot")

    def test_space_then_marker_across_chunks(self):
        out = self.collect(["supports it", " ", "[molecular-integrity]."])
        self.assertEqual(out, "supports it.")

    def test_truncated_marker_dropped_at_flush(self):
        out = self.collect(["see more", " [antibody-valid"])
        self.assertEqual(out, "see more")

    def test_never_emits_partial_slug_midstream(self):
        scrubber = StreamScrubber()
        emitted = scrubber.feed("x [molecular-integ")
        self.assertNotIn("[", emitted)

    def test_plain_text_passes_through_incrementally(self):
        scrubber = StreamScrubber()
        self.assertEqual(scrubber.feed("hello "), "hello")
        self.assertEqual(scrubber.feed("world"), " world")
        self.assertEqual(scrubber.flush(), "")


# Four concepts covering the shapes the numbering has to survive: IPI's own
# framework, which publishes nothing citable; a concept with one paper; one
# with two; and a fourth sharing a paper with the third.
SOURCES = {
    "four-dimensional-framework": [],
    "what-is-binding": ["https://example.org/a"],
    "selectivity": ["https://example.org/b", "https://example.org/c"],
    "molecular-integrity": ["https://example.org/b"],
}


class NumberedScrubberTests(unittest.TestCase):
    def collect(self, chunks):
        scrubber = StreamScrubber(lambda cid: SOURCES.get(cid, []))
        parts = [scrubber.feed(chunk) for chunk in chunks]
        parts.append(scrubber.flush())
        return "".join(parts), scrubber

    def scrub(self, text):
        return self.collect([text])[0]

    def test_marker_becomes_an_ordinal(self):
        self.assertEqual(
            self.scrub("Binding is measured directly [what-is-binding]."),
            "Binding is measured directly [1].",
        )

    def test_second_concept_takes_the_next_number(self):
        out = self.scrub("First [what-is-binding]. Then [molecular-integrity].")
        self.assertEqual(out, "First [1]. Then [2].")

    def test_repeat_citation_reuses_its_number(self):
        out = self.scrub("One [what-is-binding]. Two [what-is-binding].")
        self.assertEqual(out, "One [1]. Two [1].")

    def test_concept_with_two_papers_renders_both(self):
        out = self.scrub("Paralogs matter [selectivity].")
        self.assertEqual(out, "Paralogs matter [1, 2].")

    def test_shared_paper_shares_a_number(self):
        # selectivity takes 1 and 2; molecular-integrity's only paper is
        # selectivity's first, so it renumbers to nothing new.
        out = self.scrub("Wide [selectivity]. Narrow [molecular-integrity].")
        self.assertEqual(out, "Wide [1, 2]. Narrow [1].")

    def test_concept_without_a_citable_source_drops_the_marker(self):
        # The IPI-authored case, which is most of the corpus: grounded, cited
        # internally, and numbered nowhere because it publishes no paper.
        out = self.scrub("IPI reads it this way [four-dimensional-framework].")
        self.assertEqual(out, "IPI reads it this way.")

    def test_unknown_id_drops_the_marker(self):
        self.assertEqual(self.scrub("A claim [not-a-concept]."), "A claim.")

    def test_multi_id_group_collects_both_numbers(self):
        out = self.scrub("Both [what-is-binding; molecular-integrity].")
        self.assertEqual(out, "Both [1, 2].")

    def test_number_survives_a_marker_split_across_chunks(self):
        out, _ = self.collect(["binding matters ", "[what-is-", "binding]", " a lot"])
        self.assertEqual(out, "binding matters [1] a lot")

    def test_literal_bracket_in_prose_is_untouched(self):
        text = "the buffer [pH 7.4!] stays"
        self.assertEqual(self.scrub(text), text)

    def test_keys_report_reading_order(self):
        _, scrubber = self.collect(["Wide [selectivity]. One [what-is-binding]."])
        self.assertEqual(
            scrubber.keys,
            ["https://example.org/b", "https://example.org/c", "https://example.org/a"],
        )

    def test_no_resolver_still_deletes(self):
        # History scrubbing and the eval scorer pass no resolver and must keep
        # the old behavior exactly, markers gone rather than numbered.
        self.assertEqual(
            scrub_text("Binding is measured directly [what-is-binding]."),
            "Binding is measured directly.",
        )


class LeakScanTests(unittest.TestCase):
    def test_clean_text_passes(self):
        self.assertEqual(leak_scan("Selectivity is about binding partners.", SLUGS), [])

    def test_slug_as_identifier_detected(self):
        self.assertTrue(leak_scan("the relevant file is molecular-integrity.", SLUGS))

    def test_slug_enumeration_detected(self):
        self.assertTrue(leak_scan("my topics: antibody-validation, what-is-binding", SLUGS))

    def test_multi_hyphen_slug_always_detected(self):
        self.assertTrue(leak_scan("this relates to five-pillars-iwgav somewhat", SLUGS))

    def test_compound_modifier_is_prose(self):
        text = "I teach from IPI's antibody-validation expertise and literature."
        self.assertEqual(leak_scan(text, SLUGS), [])

    def test_single_word_slug_not_flagged_as_prose(self):
        self.assertEqual(leak_scan("selectivity matters in every assay", SLUGS), [])

    def test_surviving_marker_group_detected(self):
        self.assertTrue(leak_scan("as noted [what-is-binding]", SLUGS))

    def test_ordinal_marker_is_not_a_leak(self):
        # The published form of a citation. The backstop scans the text the
        # visitor actually read, so it has to pass numbers through or every
        # sourced answer would be blocked.
        self.assertEqual(leak_scan("binding is direct [1].", SLUGS), [])

    def test_ordinal_list_is_not_a_leak(self):
        self.assertEqual(leak_scan("paralogs matter [1, 2].", SLUGS), [])

    def test_near_ordinal_group_is_still_a_leak(self):
        # Only a bare ordinal run is carved out; anything else in the brackets
        # falls back to being a finding.
        self.assertTrue(leak_scan("as noted [1a]", SLUGS))

    def test_internal_label_detected(self):
        self.assertTrue(leak_scan("per the chatbot kickoff notes", SLUGS))

    def test_paraphrased_internal_label_detected(self):
        # The exact frontmatter label is not what a leaked reply says. A model
        # that has never seen the label still reaches for the surname and noun.
        for text in ("per Moshinsky's notes", "IPI's internal draft says",
                     "recorded in the kickoff notes", "released under IPI-CHR-002"):
            self.assertTrue(leak_scan(text, SLUGS), text)

    def test_ordinary_scientific_prose_is_not_a_leak(self):
        # The bound on the list above. leak_scan is fail-closed and replaces the
        # whole reply, so a marker that fires on validation prose destroys
        # correct answers. This is the test that fails if someone adds bare
        # "manuscript", "draft", "notes", or "unpublished" to the tuple.
        for text in ("the 2016 manuscript proposing five pillars",
                     "a draft guideline from the working group",
                     "the authors' notes on antibody selection",
                     "unpublished data was excluded from the review"):
            self.assertEqual(leak_scan(text, SLUGS), [], text)

    def test_zero_width_obfuscation_detected(self):
        self.assertTrue(leak_scan("molecular-\u200bintegrity", SLUGS))

    def test_case_insensitive(self):
        self.assertTrue(leak_scan("Molecular-Integrity", SLUGS))

    def test_internal_label_detected_in_any_source_field(self):
        # The widget shows short, journal and title alongside the label, and
        # the API scans every one of them. A field the scan skips is a field
        # that reaches the visitor unchecked.
        for field in ("D. Moshinsky", "chatbot kickoff notes",
                      "IPI 4D framework, internal draft",
                      "IPI-CHR-001, internal antibody QC standard"):
            self.assertTrue(leak_scan(field, SLUGS), field)

    def test_internal_sop_identifier_detected_in_prose(self):
        # The assay concepts are grounded in IPI's release-gate SOP, so its
        # identifier is now reachable from the model's context and has to be
        # caught in a reply, not only in a source field.
        self.assertTrue(leak_scan("Batches are released under IPI-CHR-001.", SLUGS))

    def test_slug_hidden_in_a_source_title_detected(self):
        self.assertTrue(leak_scan("adapted from five-pillars-iwgav", SLUGS))

    def test_ordinary_citation_fields_are_clean(self):
        for field in ("Uhlén 2016", "Nat Methods",
                      "A proposal for validation of antibodies",
                      "Immunobiology: The Immune System in Health and Disease"):
            self.assertEqual(leak_scan(field, SLUGS), [], field)


class IsPublishableTests(unittest.TestCase):
    def test_real_paper_is_publishable(self):
        self.assertTrue(is_publishable({
            "url": "https://doi.org/10.7554/eLife.91645",
            "label": "Ayoubi R, et al. eLife. 2023;12:RP91645.",
        }))

    def test_source_without_a_url_is_withheld(self):
        self.assertFalse(is_publishable({"label": "Ayoubi R, et al. eLife. 2023."}))

    def test_internal_label_withheld_even_carrying_a_url(self):
        # The regression this guards: withholding on the absent url alone
        # publishes IPI's unpublished material the day someone adds one.
        for label in ("D. Moshinsky, chatbot kickoff notes, 14 July 2026",
                      "IPI 4D framework, internal draft",
                      "Notes from D. MOSHINSKY"):
            self.assertFalse(
                is_publishable({"url": "https://example.org", "label": label}),
                label,
            )

    def test_missing_label_with_a_url_is_publishable(self):
        self.assertTrue(is_publishable({"url": "https://example.org"}))


if __name__ == "__main__":
    unittest.main()
