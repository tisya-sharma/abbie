"""Unit tests for the output guardrail. Run without an API key:

    python3 -m unittest packages.guardrail.test_guardrail
"""

import unittest

from packages.guardrail import StreamScrubber, leak_scan, scrub_text

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

    def test_internal_label_detected(self):
        self.assertTrue(leak_scan("per the chatbot kickoff notes", SLUGS))

    def test_zero_width_obfuscation_detected(self):
        self.assertTrue(leak_scan("molecular-\u200bintegrity", SLUGS))

    def test_case_insensitive(self):
        self.assertTrue(leak_scan("Molecular-Integrity", SLUGS))

    def test_internal_label_detected_in_any_source_field(self):
        # The widget shows short, journal and title alongside the label, and
        # the API scans every one of them. A field the scan skips is a field
        # that reaches the visitor unchecked.
        for field in ("D. Moshinsky", "chatbot kickoff notes",
                      "IPI 4D framework, internal draft"):
            self.assertTrue(leak_scan(field, SLUGS), field)

    def test_slug_hidden_in_a_source_title_detected(self):
        self.assertTrue(leak_scan("adapted from five-pillars-iwgav", SLUGS))

    def test_ordinary_citation_fields_are_clean(self):
        for field in ("Uhlén 2016", "Nat Methods",
                      "A proposal for validation of antibodies",
                      "Immunobiology: The Immune System in Health and Disease"):
            self.assertEqual(leak_scan(field, SLUGS), [], field)


if __name__ == "__main__":
    unittest.main()
