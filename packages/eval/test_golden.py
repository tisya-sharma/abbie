"""Schema checks on the golden set. Run without an API key:

    python3 -m unittest packages.eval.test_golden

Nothing validated golden.yaml against the corpus before this file. A must_cite
naming a concept that does not exist scores as a permanent failure, and the only
place it surfaced was a paid eval run, several minutes and a few hundred model
calls after the typo was written. These checks run free and in CI instead.

They are deliberately structural. Whether a case is a good case is a judgment
the notes field carries; whether it can ever pass is arithmetic.
"""

import unittest

from packages.corpus_loader import load_corpus
from packages.eval.checks import run_property_checks
from packages.eval.run import load_golden

BEHAVIORS = {"answer", "abstain", "refuse", "redirect"}


class MustCiteTests(unittest.TestCase):
    """Every required citation has to name a concept that ships.

    Validated against the public build rather than the full one, because
    extract_citations resolves against whatever the running build loaded. A
    must_cite pointing at a pre-publication concept could never pass at runtime.
    """

    def setUp(self):
        _, self.cases = load_golden()
        self.concepts = load_corpus()

    def test_every_must_cite_id_resolves_to_a_concept(self):
        # Collected rather than asserted one at a time, because assertIn renders
        # the whole corpus dict into the failure and buries the id that broke.
        unknown = [
            f"{case['id']} -> {cid}"
            for case in self.cases
            for cid in case.get("must_cite", [])
            if cid not in self.concepts
        ]
        self.assertEqual(unknown, [], f"must_cite names no such concept: {unknown}")

    def test_must_cite_is_empty_where_it_would_be_ignored(self):
        """score_case applies must_cite only to answer cases.

        A required citation on a redirect or refuse case is not a stricter test,
        it is a silently dead one, so the set should not carry any.
        """
        for case in self.cases:
            if case["behavior"] != "answer":
                self.assertEqual(
                    case.get("must_cite", []),
                    [],
                    f"{case['id']}: must_cite on a {case['behavior']} case is never read",
                )


class CaseShapeTests(unittest.TestCase):
    def setUp(self):
        _, self.cases = load_golden()

    def test_case_ids_are_unique(self):
        ids = [case["id"] for case in self.cases]
        self.assertEqual(sorted(ids), sorted(set(ids)))

    def test_every_case_declares_a_known_behavior(self):
        for case in self.cases:
            self.assertIn(case["behavior"], BEHAVIORS, case["id"])

    def test_every_case_carries_a_question_and_an_ideal(self):
        for case in self.cases:
            self.assertTrue(case.get("question"), f"{case['id']}: no question")
            self.assertTrue(case.get("ideal"), f"{case['id']}: no ideal")

    def test_form_is_present_exactly_on_answer_cases(self):
        """Shape checks key off the authored form, and only answer cases have one.

        A form tag on a non-answer case never reaches word_budget; a missing one
        on an answer case drops that case out of the router's form_accuracy
        denominator without anything saying so.
        """
        for case in self.cases:
            has_form = "form" in case
            self.assertEqual(
                has_form,
                case["behavior"] == "answer",
                f"{case['id']}: form on a {case['behavior']} case",
            )


class PropertyCheckSpecTests(unittest.TestCase):
    """run_property_checks raises on a name it does not implement.

    That is the right behavior and the wrong moment: it fires mid-run, after the
    model calls have been paid for. Dispatching every spec against a fixed reply
    reaches the same branch for free.
    """

    def test_every_declared_check_dispatches(self):
        spec, _ = load_golden()
        concepts = load_corpus()
        reply = "You can look at what makes a signal attributable [selectivity]."
        for behavior, checks in spec.items():
            for form in (None, "definitional"):
                run_property_checks(reply, checks, concepts, form=form)


if __name__ == "__main__":
    unittest.main()
