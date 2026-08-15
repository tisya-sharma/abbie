"""Unit tests for the voice checks. Run without an API key:

    python3 -m unittest packages.eval.test_checks

These cover the checks added after eval-20260815-191427, where all eighteen
redirect cases passed while reading cold and templated. Each test names the
production reply that motivated it, so a future loosening has to argue with the
evidence rather than with a preference.
"""

import unittest

from packages.eval.checks import run_property_checks

STOCK = ["antibody validation expertise and the published literature"]


def check(text: str, spec: list) -> dict:
    """Score one reply, with no corpus since none of these checks read it."""
    return run_property_checks(text, spec, {})


class BareRefusalOpenerTests(unittest.TestCase):
    """Opening by refusing, before answering anything.

    Eight of the eighteen recorded redirects did this and none of the authored
    ideals did. The discriminator is punctuation after "No", not the word.
    """

    SPEC = ["no_bare_refusal_opener"]

    def test_observed_refusal_openers_are_flagged(self):
        for opener in (
            "No — I don't take positions on political administrations.",
            "No, I can't predict sports outcomes.",
            "No. I keep my internal files private.",
            "No—I can't do that.",
            "No; that is not something I share.",
            "No: I cannot provide that.",
            "No - I cannot show internal documents.",
            "  No — leading whitespace still counts.",
        ):
            self.assertFalse(check(opener, self.SPEC)["no_bare_refusal_opener"], opener)

    def test_no_idea_survives(self):
        # The weather reply, and the one bare-No opening worth keeping: it is
        # answering the question rather than declining to.
        text = "No idea, I'm made entirely of documents and have never been outside."
        self.assertTrue(check(text, self.SPEC)["no_bare_refusal_opener"])

    def test_word_starting_with_no_survives(self):
        text = "Nothing to override, I'm just here to talk antibodies."
        self.assertTrue(check(text, self.SPEC)["no_bare_refusal_opener"])

    def test_refusal_later_in_the_reply_is_not_an_opener(self):
        text = "I like both, honestly. No, I can't pick a favorite."
        self.assertTrue(check(text, self.SPEC)["no_bare_refusal_opener"])


class StockPhraseTests(unittest.TestCase):
    """The clause thirteen of eighteen replies reached for."""

    SPEC = [{"no_stock_phrase": STOCK}]

    def test_the_worn_out_clause_is_flagged(self):
        text = ("I teach from IPI's antibody validation expertise and the published"
                " literature, and I cite papers when they support an answer.")
        self.assertFalse(check(text, self.SPEC)["no_stock_phrase"])

    def test_matching_ignores_case_and_line_wrapping(self):
        # golden.yaml ideals are block scalars, so the phrase arrives wrapped.
        text = ("I teach from IPI's Antibody Validation Expertise\nand the Published"
                " Literature.")
        self.assertFalse(check(text, self.SPEC)["no_stock_phrase"])

    def test_saying_the_same_thing_differently_passes(self):
        text = ("IPI's own validation work, plus the published literature, and any"
                " paper behind an answer shows up linked underneath.")
        self.assertTrue(check(text, self.SPEC)["no_stock_phrase"])


class BannedOpenerTests(unittest.TestCase):
    """The check existed and the production reply walked past it anyway."""

    SPEC = [{"no_banned_openers": ["Great question", "Nice question"]}]

    def test_exact_casing_is_flagged(self):
        self.assertFalse(check("Nice question — I'm here to help.", self.SPEC)
                         ["no_banned_openers"])

    def test_lowercase_is_flagged(self):
        self.assertFalse(check("nice question, let me explain.", self.SPEC)
                         ["no_banned_openers"])

    def test_bolded_is_flagged(self):
        self.assertFalse(check("**Nice question** — here is the answer.", self.SPEC)
                         ["no_banned_openers"])

    def test_quoted_is_flagged(self):
        self.assertFalse(check('"Nice question" is what I would say.', self.SPEC)
                         ["no_banned_openers"])

    def test_ordinary_opening_passes(self):
        self.assertTrue(check("Honestly, I like both.", self.SPEC)["no_banned_openers"])


class BoldTermTests(unittest.TestCase):
    """Bold marks IPI's four dimensions and nothing else.

    The research against emphasis measures a model choosing what to stress,
    where misplaced highlighting hurts comprehension. A closed set makes no
    choice, and this check is what keeps the set closed.
    """

    SPEC = [{"bold_terms_allowed": ["molecular integrity", "target engagement",
                                    "selectivity", "experimental readout",
                                    "integrity", "engagement", "readout"]}]

    def test_dimension_in_full_passes(self):
        text = "IPI organizes evidence along **molecular integrity** and **selectivity**."
        self.assertTrue(check(text, self.SPEC)["bold_terms_allowed"])

    def test_short_form_passes(self):
        text = "**Integrity** says nothing about whether the antibody binds."
        self.assertTrue(check(text, self.SPEC)["bold_terms_allowed"])

    def test_sentence_initial_capital_passes(self):
        # Capitalized only because it opens a sentence, which is ordinary
        # English rather than the proper-noun casing being retired.
        text = "**Selectivity** is a separate question from engagement."
        self.assertTrue(check(text, self.SPEC)["bold_terms_allowed"])

    def test_emphasis_on_anything_else_is_flagged(self):
        text = "This is **really important** for your experiment."
        self.assertFalse(check(text, self.SPEC)["bold_terms_allowed"])

    def test_one_stray_span_among_valid_ones_is_flagged(self):
        text = "**selectivity** matters, and so does **sample preparation**."
        self.assertFalse(check(text, self.SPEC)["bold_terms_allowed"])

    def test_unbolded_prose_passes(self):
        self.assertTrue(check("No emphasis anywhere here.", self.SPEC)
                        ["bold_terms_allowed"])


class WarmthBoundTests(unittest.TestCase):
    def test_exclamation_marks_within_the_bound(self):
        spec = [{"max_exclamation_marks": 2}]
        self.assertTrue(check("I'm well, thanks! What are you working on?", spec)
                        ["max_exclamation_marks"])

    def test_exclamation_marks_over_the_bound(self):
        spec = [{"max_exclamation_marks": 2}]
        self.assertFalse(check("Hi! Great! Wonderful!", spec)["max_exclamation_marks"])

    def test_one_ask_passes(self):
        spec = [{"max_questions": 1}]
        self.assertTrue(check("I can't look that up. What are you working on?", spec)
                        ["max_questions"])

    def test_two_asks_are_flagged(self):
        # The observed shape: decline, then stack a second question on top.
        spec = [{"max_questions": 1}]
        text = "Are you validating an antibody? Or do you want the general case?"
        self.assertFalse(check(text, spec)["max_questions"])


if __name__ == "__main__":
    unittest.main()
