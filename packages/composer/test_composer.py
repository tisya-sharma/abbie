"""Unit tests for reply composition. Run without an API key:

    python3 -m unittest packages.composer.test_composer
"""

import unittest

from packages.composer import DEFAULT_ABSTAIN_SUBJECT, _clean_subject


class CleanSubjectTests(unittest.TestCase):
    """The abstain subject is the one visitor-supplied string that reaches a
    reply verbatim, with no model between the question and the page.
    """

    def test_named_reagent_passes_through(self):
        self.assertEqual(
            _clean_subject("clone 4B2 against STAT3"), "clone 4B2 against STAT3"
        )

    def test_catalog_number_passes_through(self):
        self.assertEqual(_clean_subject("AB-88231"), "AB-88231")

    def test_ipi_reagent_passes_through(self):
        # The guard must not fire on IPI's own products, which are exactly what
        # the abstention exists to talk about.
        self.assertEqual(
            _clean_subject("the IPI anti-TP53 rabbit antibody"),
            "the IPI anti-TP53 rabbit antibody",
        )

    def test_word_containing_a_document_word_passes_through(self):
        # "standardize" contains "standard"; matching whole words is what keeps
        # ordinary reagent phrasing out of the fallback.
        self.assertEqual(
            _clean_subject("the standardized control lot"),
            "the standardized control lot",
        )

    def test_manuscript_request_falls_back(self):
        self.assertEqual(_clean_subject("Deb's manuscript"), DEFAULT_ABSTAIN_SUBJECT)

    def test_draft_request_falls_back(self):
        self.assertEqual(
            _clean_subject("the IPI 4D framework draft"), DEFAULT_ABSTAIN_SUBJECT
        )

    def test_internal_standard_request_falls_back(self):
        self.assertEqual(
            _clean_subject("the antibody QC standard"), DEFAULT_ABSTAIN_SUBJECT
        )

    def test_internal_identifier_falls_back(self):
        self.assertEqual(_clean_subject("IPI-CHR-001"), DEFAULT_ABSTAIN_SUBJECT)

    def test_empty_subject_falls_back(self):
        self.assertEqual(_clean_subject(None), DEFAULT_ABSTAIN_SUBJECT)

    def test_overlong_subject_falls_back(self):
        self.assertEqual(
            _clean_subject(" ".join(["word"] * 13)), DEFAULT_ABSTAIN_SUBJECT
        )

    def test_brackets_are_stripped(self):
        self.assertEqual(_clean_subject("[what-is-binding]"), "what-is-binding")


if __name__ == "__main__":
    unittest.main()
