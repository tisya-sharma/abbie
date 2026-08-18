"""Unit tests for the paired run comparison. Run without an API key:

    python3 -m unittest packages.eval.test_compare

The blocking relative gate in roadmap.md is defined over `answer` cases, but
compare.py compared every shared case until --behavior existed, so the
restriction was applied by hand to the printed flip ids and the printed p-value
stayed pooled across all four behaviors. The CLI tests below pin the difference
that pooling makes: the same pair of runs is significant unfiltered and shows no
discordant answer case at all under --behavior answer.

The payloads are synthetic and carry only the fields compare.py reads, so a new
field in the results schema cannot break them.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from packages.eval.compare import exact_mcnemar, paired_verdicts

BASELINE_CASES = [
    ("qa-1", "answer", True),
    ("qa-2", "answer", True),
    ("qa-3", "answer", True),
    ("qa-4", "answer", True),
    ("qr-1", "redirect", True),
    ("qr-2", "redirect", True),
    ("qr-3", "redirect", True),
    ("qr-4", "redirect", True),
    ("qr-5", "redirect", True),
    ("qr-6", "redirect", True),
]

# Every redirect regresses, every answer holds: the pooled test fires, the
# pre-registered answer-only test has nothing to look at.
REDIRECT_REGRESSION_CASES = [
    (cid, behavior, behavior != "redirect") for cid, behavior, _ in BASELINE_CASES
]


def payload(run_id: str, cases: list[tuple[str, str, bool]]) -> dict:
    """A one-run results payload holding only the fields compare.py reads."""
    return {
        "run_id": run_id,
        "runs": [
            {
                "model": "gpt-5-mini",
                "config": "routed",
                "cases": [
                    {"id": cid, "behavior_expected": behavior, "passed": passed}
                    for cid, behavior, passed in cases
                ],
            }
        ],
    }


def run_cli(cases_a: list, cases_b: list, *flags: str) -> str:
    """Drive main() over two temp results files and capture what it printed.

    Goes through main() rather than the pieces because the header line and the
    flip listing are the transcript a gate decision is read from, and neither is
    returned by anything.
    """
    from packages.eval.compare import main

    with tempfile.TemporaryDirectory() as tmp:
        path_a = Path(tmp) / "eval-a.json"
        path_b = Path(tmp) / "eval-b.json"
        path_a.write_text(json.dumps(payload("eval-a", cases_a)), encoding="utf-8")
        path_b.write_text(json.dumps(payload("eval-b", cases_b)), encoding="utf-8")
        argv = ["compare.py", str(path_a), str(path_b), *flags]
        buffer = io.StringIO()
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(buffer):
            main()
        return buffer.getvalue()


class ExactMcNemarTests(unittest.TestCase):
    """The arithmetic, on counts small enough to check by hand."""

    def test_no_discordant_pairs_is_certain_agreement(self):
        self.assertEqual(exact_mcnemar(0, 0), 1.0)

    def test_symmetric_flips_clamp_at_one(self):
        # n=4, k=2: 2 * (1+4+6)/16 = 1.375 before the clamp.
        self.assertEqual(exact_mcnemar(2, 2), 1.0)

    def test_asymmetric_split_matches_the_binomial_tail(self):
        # n=4, k=1: 2 * (1+4)/16.
        self.assertAlmostEqual(exact_mcnemar(1, 3), 0.625)

    def test_five_one_way_still_misses_the_five_percent_line(self):
        # The detection floor quoted in demo-runbook.md: 2 * 1/32.
        self.assertAlmostEqual(exact_mcnemar(0, 5), 0.0625)

    def test_six_one_way_is_the_smallest_significant_result(self):
        # 2 * 1/64, the first count that clears 5%.
        self.assertAlmostEqual(exact_mcnemar(6, 0), 0.03125)
        self.assertLess(exact_mcnemar(6, 0), 0.05)


class PairedVerdictsTests(unittest.TestCase):
    """Which cases each side contributes, with and without the filter."""

    def setUp(self):
        self.run_a = payload("eval-a", BASELINE_CASES)["runs"][0]
        self.run_b = payload("eval-b", REDIRECT_REGRESSION_CASES)["runs"][0]

    def test_no_behavior_keeps_every_case(self):
        verdicts_a, verdicts_b = paired_verdicts(self.run_a, self.run_b, None)
        self.assertEqual(len(verdicts_a), 10)
        self.assertEqual(len(verdicts_b), 10)
        self.assertIn("qr-1", verdicts_a)

    def test_answer_filter_drops_the_other_behaviors(self):
        verdicts_a, verdicts_b = paired_verdicts(self.run_a, self.run_b, "answer")
        self.assertEqual(sorted(verdicts_a), ["qa-1", "qa-2", "qa-3", "qa-4"])
        self.assertEqual(sorted(verdicts_b), ["qa-1", "qa-2", "qa-3", "qa-4"])

    def test_redirect_filter_selects_the_regressed_side(self):
        verdicts_a, verdicts_b = paired_verdicts(self.run_a, self.run_b, "redirect")
        self.assertTrue(all(verdicts_a.values()))
        self.assertFalse(any(verdicts_b.values()))

    def test_case_present_on_one_side_only_survives_the_filter(self):
        # Kept so main() can report it; dropping it here would hide a golden-set
        # change behind a smaller shared set.
        run_b = payload("eval-b", BASELINE_CASES + [("qa-new", "answer", True)])["runs"][0]
        _, verdicts_b = paired_verdicts(self.run_a, run_b, "answer")
        self.assertIn("qa-new", verdicts_b)

    def test_disagreeing_behavior_expected_stops_the_comparison(self):
        run_b = payload("eval-b", [("qa-1", "redirect", True)])["runs"][0]
        with self.assertRaises(SystemExit) as raised:
            paired_verdicts(self.run_a, run_b, "answer")
        message = str(raised.exception)
        self.assertIn("qa-1", message)
        self.assertIn("answer", message)
        self.assertIn("redirect", message)

    def test_behavior_expected_is_only_compared_under_the_filter(self):
        # An unfiltered comparison never reads the field, so a relabeled case
        # cannot start failing runs that worked before the flag existed.
        run_b = payload("eval-b", [("qa-1", "redirect", True)])["runs"][0]
        _, verdicts_b = paired_verdicts(self.run_a, run_b, None)
        self.assertEqual(verdicts_b, {"qa-1": True})


class CliOutputTests(unittest.TestCase):
    """What a gate transcript actually shows."""

    def test_unfiltered_output_pools_all_four_behaviors(self):
        out = run_cli(BASELINE_CASES, REDIRECT_REGRESSION_CASES)
        self.assertNotIn("restricted to", out)
        self.assertIn("A: gpt-5-mini/routed (eval-a)  10/10", out)
        self.assertIn("B: gpt-5-mini/routed (eval-b)  4/10", out)
        self.assertIn("flips: +0/-6, exact McNemar p = 0.031", out)
        self.assertIn("verdict: statistically distinguishable", out)

    def test_answer_filter_excludes_the_redirect_flips(self):
        out = run_cli(BASELINE_CASES, REDIRECT_REGRESSION_CASES, "--behavior", "answer")
        self.assertIn("restricted to behavior_expected = answer: 4 shared case(s)", out)
        self.assertIn("no discordant cases", out)
        self.assertIn("flips: +0/-0, exact McNemar p = 1.000", out)
        self.assertNotIn("qr-", out)

    def test_answer_flips_are_still_reported_under_the_filter(self):
        cases_b = [
            ("qa-1", "answer", False),
            ("qa-2", "answer", True),
            ("qa-3", "answer", True),
            ("qa-4", "answer", True),
            ("qr-1", "redirect", False),
            ("qr-2", "redirect", True),
            ("qr-3", "redirect", True),
            ("qr-4", "redirect", True),
            ("qr-5", "redirect", True),
            ("qr-6", "redirect", True),
        ]
        out = run_cli(BASELINE_CASES, cases_b, "--behavior", "answer")
        self.assertIn("pass -> fail  qa-1", out)
        self.assertNotIn("qr-1", out)
        self.assertIn("flips: +0/-1, exact McNemar p = 1.000", out)

    def test_one_sided_case_is_named_under_the_filter(self):
        cases_b = BASELINE_CASES + [("qa-new", "answer", True)]
        out = run_cli(BASELINE_CASES, cases_b, "--behavior", "answer")
        self.assertIn("ignoring 1 case(s) present on one side only: qa-new", out)
        self.assertIn("restricted to behavior_expected = answer: 4 shared case(s)", out)

    def test_a_behavior_with_no_cases_exits_naming_the_behavior(self):
        with self.assertRaises(SystemExit) as raised:
            run_cli(BASELINE_CASES, BASELINE_CASES, "--behavior", "abstain")
        self.assertIn("behavior_expected = abstain", str(raised.exception))

    def test_an_unknown_behavior_is_rejected_by_the_parser(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            run_cli(BASELINE_CASES, BASELINE_CASES, "--behavior", "answers")


if __name__ == "__main__":
    unittest.main()
