"""Unit tests for the model-graded judge. Run without an API key:

    python3 -m unittest packages.eval.test_judge

Every call here goes through a recording fake, so the suite stays free and
offline. The two properties worth defending are that a judgment can never
change whether a case passed, and that a second identical judgment is free.
"""

import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from openai import APIConnectionError

from packages.eval import judge, run

CASE = {
    "id": "q-example",
    "question": "What is an antibody?",
    "behavior": "redirect",
    "ideal": "A Y-shaped protein whose tips grip one patch on one molecule.\n",
}

REPLY = "I only talk about antibodies, ask me one and I will tell you what I know."

GRADED = {
    "covers_ideal": True,
    "contradicts_ideal": False,
    "rationale": "Carries the Y shape and the one-patch grip.",
}


class RecordingClient:
    """Returns a canned completion and counts how often it was asked for one."""

    def __init__(self, content: str = json.dumps(GRADED), finish_reason: str = "stop",
                 error: Exception | None = None):
        self.calls = 0
        self.messages: list[dict] = []
        self.models: list[str] = []
        outer = self

        class Completions:
            def create(self, **kwargs):
                outer.calls += 1
                outer.messages = kwargs["messages"]
                outer.models.append(kwargs["model"])
                if error is not None:
                    raise error
                return types.SimpleNamespace(
                    choices=[
                        types.SimpleNamespace(
                            message=types.SimpleNamespace(content=content),
                            finish_reason=finish_reason,
                        )
                    ]
                )

        self.chat = types.SimpleNamespace(completions=Completions())


def connection_error() -> APIConnectionError:
    """One real SDK error, so the except clause is exercised as written."""
    return APIConnectionError(request=types.SimpleNamespace())


def trial(judgment: dict | None) -> dict:
    """The one field of a scored trial that _fold_judge reads."""
    return {"judge": judgment}


class PromptTests(unittest.TestCase):
    """The rubric is the contract: grade against the ideal, not against priors."""

    def test_prompt_carries_the_question_the_ideal_and_the_reply(self):
        messages = judge.build_judge_messages(CASE, REPLY)
        user = messages[-1]["content"]
        self.assertIn(CASE["question"], user)
        self.assertIn(CASE["ideal"].rstrip(), user)
        self.assertIn(REPLY, user)

    def test_rubric_pins_the_ideal_as_the_only_standard(self):
        system = judge.build_judge_messages(CASE, REPLY)[0]["content"]
        # Joined on whitespace so rewrapping the prompt does not fail the test.
        flat = " ".join(system.lower().split())
        self.assertIn("never grade against your own knowledge", flat)
        self.assertIn("the ideal is the only standard of correctness", flat)

    def test_the_prompt_is_deterministic(self):
        self.assertEqual(
            judge.build_judge_messages(CASE, REPLY),
            judge.build_judge_messages(CASE, REPLY),
        )


class ParseTests(unittest.TestCase):
    """A judge that raises would take the scoring loop down with it, so no path
    out of judge_reply raises: every failure becomes an error dict.
    """

    def test_well_formed_response_becomes_a_verdict(self):
        result = judge.judge_reply(RecordingClient(), "judge-model", CASE, REPLY)
        self.assertEqual(result["model"], "judge-model")
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["rationale"], GRADED["rationale"])

    def test_a_contradiction_fails_even_when_coverage_holds(self):
        # The verdict is derived rather than asked for, so the judge cannot pass
        # a reply it has just said contradicts the ideal.
        content = json.dumps({**GRADED, "contradicts_ideal": True})
        result = judge.judge_reply(
            RecordingClient(content=content), "judge-model", CASE, REPLY
        )
        self.assertEqual(result["verdict"], "fail")

    def test_missing_coverage_fails(self):
        content = json.dumps({**GRADED, "covers_ideal": False})
        result = judge.judge_reply(
            RecordingClient(content=content), "judge-model", CASE, REPLY
        )
        self.assertEqual(result["verdict"], "fail")

    def test_malformed_json_becomes_an_error_dict(self):
        result = judge.judge_reply(
            RecordingClient(content="not json at all"), "judge-model", CASE, REPLY
        )
        self.assertEqual(result, {"model": "judge-model", "error": "bad_json"})

    def test_missing_fields_become_an_error_dict(self):
        result = judge.judge_reply(
            RecordingClient(content=json.dumps({"verdict": "pass"})),
            "judge-model", CASE, REPLY,
        )
        self.assertEqual(result, {"model": "judge-model", "error": "bad_fields"})

    def test_truncated_output_becomes_an_error_dict(self):
        result = judge.judge_reply(
            RecordingClient(finish_reason="length"), "judge-model", CASE, REPLY
        )
        self.assertEqual(result, {"model": "judge-model", "error": "length"})

    def test_api_error_becomes_an_error_dict(self):
        result = judge.judge_reply(
            RecordingClient(error=connection_error()), "judge-model", CASE, REPLY
        )
        self.assertEqual(result["model"], "judge-model")
        self.assertTrue(result["error"].startswith("api_error"))


class FlagOffTests(unittest.TestCase):
    """Off is the default, and off has to mean untouched: an unjudged run must
    stay byte-identical to the results already committed as baselines.
    """

    def test_resolve_returns_none_when_the_flag_is_off(self):
        self.assertIsNone(run.resolve_judge_model(False, "gpt-5-mini"))
        self.assertEqual(run.resolve_judge_model(True, "gpt-5-mini"), "gpt-5-mini")

    def test_no_judge_model_means_no_call_and_no_judgment(self):
        client = RecordingClient()
        self.assertIsNone(run.maybe_judge(client, CASE, REPLY, None, True))
        self.assertEqual(client.calls, 0)

    def test_unjudged_trials_aggregate_to_judge_none(self):
        record = run.aggregate_trials(CASE, [scored_trial(passed=True)])
        self.assertIsNone(record["judge"])

    def test_summary_has_no_judge_field_without_judging(self):
        record = run.aggregate_trials(CASE, [scored_trial(passed=True)])
        self.assertNotIn("judge_pass_rate", run.summarize([record]))


class CacheTests(unittest.TestCase):
    """A re-scored run has to cost nothing, which is the whole reason the judge
    is cached rather than re-bought on every pass over the same replies.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        patcher = mock.patch.object(run, "CACHE_DIR", Path(self.tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_second_identical_judgment_never_reaches_the_client(self):
        client = RecordingClient()
        first = run.maybe_judge(client, CASE, REPLY, "judge-model", True)
        second = run.maybe_judge(client, CASE, REPLY, "judge-model", True)
        self.assertEqual(client.calls, 1)
        self.assertEqual(first, second)

    def test_no_cache_draws_a_fresh_judgment(self):
        client = RecordingClient()
        run.maybe_judge(client, CASE, REPLY, "judge-model", False)
        run.maybe_judge(client, CASE, REPLY, "judge-model", False)
        self.assertEqual(client.calls, 2)

    def test_errors_are_not_cached(self):
        # An outage is a fact about one moment, not about the reply. Caching it
        # would make the next run replay the failure for free.
        client = RecordingClient(error=connection_error())
        run.maybe_judge(client, CASE, REPLY, "judge-model", True)
        run.maybe_judge(client, CASE, REPLY, "judge-model", True)
        self.assertEqual(client.calls, 2)

    def key(self, case: dict, reply: str, model: str = "judge-model") -> str:
        return run.judge_cache_key(
            model, case["question"], judge.build_judge_messages(case, reply)
        )

    def test_key_changes_with_the_judge_model(self):
        self.assertNotEqual(
            self.key(CASE, REPLY), self.key(CASE, REPLY, "other-model")
        )

    def test_key_changes_with_the_reply(self):
        self.assertNotEqual(self.key(CASE, REPLY), self.key(CASE, REPLY + " more"))

    def test_key_changes_with_the_ideal(self):
        edited = {**CASE, "ideal": "A different ideal entirely.\n"}
        self.assertNotEqual(self.key(CASE, REPLY), self.key(edited, REPLY))

    def test_key_changes_when_the_rubric_is_edited(self):
        before = self.key(CASE, REPLY)
        with mock.patch.object(judge, "JUDGE_SYSTEM", "a rewritten rubric"):
            after = self.key(CASE, REPLY)
        self.assertNotEqual(before, after)


def scored_trial(passed: bool, judgment: dict | None = None) -> dict:
    """One scored trial, measured fields included, ready for aggregate_trials."""
    measured = {
        "reply": REPLY if passed else "cannot help with clinical diagnosis",
        "finish_reason": "stop",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "reasoning_tokens": 0,
        "latency_ms": 100,
    }
    return run.score_trial(CASE, measured, "gpt-5-mini", {}, {}, judgment)


class NonBlockingTests(unittest.TestCase):
    """The model-graded tier is tracked and never gates. A judge verdict that
    disagreed with the checks would otherwise quietly become a release blocker.
    """

    def test_a_failing_judgment_leaves_the_case_passing(self):
        failing = {"model": "judge-model", "verdict": "fail",
                   "rationale": "misses the ideal's caveat",
                   "covers_ideal": False, "contradicts_ideal": False}
        scored = scored_trial(passed=True, judgment=failing)
        self.assertTrue(scored["passed"])
        self.assertEqual(scored["failures"], [])
        self.assertEqual(scored["judge"], failing)

        record = run.aggregate_trials(CASE, [scored])
        self.assertTrue(record["passed"])
        self.assertEqual(record["failures"], [])
        self.assertEqual(record["judge"]["verdict"], "fail")

    def test_a_passing_judgment_does_not_rescue_a_failing_case(self):
        passing = {"model": "judge-model", "verdict": "pass", "rationale": "fine",
                   "covers_ideal": True, "contradicts_ideal": False}
        record = run.aggregate_trials(CASE, [scored_trial(False, passing)])
        self.assertFalse(record["passed"])
        self.assertEqual(run.summarize([record])["judge_pass_rate"], 1.0)


class FoldTests(unittest.TestCase):
    """Judgments fold across trials the way the deterministic checks do, with
    errored trials left out of the denominator rather than counted as failures.
    """

    def verdict(self, value: str) -> dict:
        return {"model": "judge-model", "verdict": value, "rationale": value,
                "covers_ideal": value == "pass", "contradicts_ideal": False}

    def test_majority_verdict_and_fraction(self):
        folded = run._fold_judge(
            [trial(self.verdict("pass")), trial(self.verdict("pass")),
             trial(self.verdict("fail"))]
        )
        self.assertEqual(folded["verdict"], "pass")
        self.assertEqual(folded["pass_fraction"], 0.667)
        self.assertEqual(folded["graded_trials"], 3)
        self.assertEqual(folded["errors"], 0)

    def test_a_tie_is_not_a_pass(self):
        folded = run._fold_judge(
            [trial(self.verdict("pass")), trial(self.verdict("fail"))]
        )
        self.assertEqual(folded["verdict"], "fail")

    def test_errored_trials_leave_the_denominator(self):
        folded = run._fold_judge(
            [trial(self.verdict("fail")),
             trial({"model": "judge-model", "error": "api_error: APIConnectionError"})]
        )
        self.assertEqual(folded["pass_fraction"], 0.0)
        self.assertEqual(folded["graded_trials"], 1)
        self.assertEqual(folded["errors"], 1)

    def test_all_errors_leave_the_verdict_unknown(self):
        folded = run._fold_judge(
            [trial({"model": "judge-model", "error": "length"})]
        )
        self.assertIsNone(folded["verdict"])
        self.assertIsNone(folded["pass_fraction"])
        self.assertEqual(folded["errors"], 1)

    def test_an_unknown_verdict_stays_out_of_the_summary_rate(self):
        record = run.aggregate_trials(
            CASE, [scored_trial(True, {"model": "judge-model", "error": "length"})]
        )
        self.assertNotIn("judge_pass_rate", run.summarize([record]))


if __name__ == "__main__":
    unittest.main()
