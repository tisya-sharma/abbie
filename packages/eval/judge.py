"""Model-graded comparison of one reply against its case's authored ideal.

The property checks in packages.eval.checks are deterministic and blind to
substance: a reply can pass every one of them while missing the point of the
question. This module is the other half — one cheap call that asks whether the
reply carries what the authored ideal carries and contradicts nothing in it.

The ideal is the only standard. A judge grading against its own knowledge of
antibodies would reward substance the corpus does not contain and penalize the
scoping the ideals were written to hold, which turns the metric into a measure
of the judge's priors rather than of Abbie. Everything else — voice, length,
citations, formatting — is already gated deterministically and is explicitly
out of the rubric here.

Results are tracked and non-blocking. Nothing returned here reaches a case's
passed field, and every failure path returns an error dict rather than raising,
so a judge outage degrades to a missing measurement instead of a failed run.
"""

from __future__ import annotations

import json

# Grading needs to read two long texts and compare them, which minimal effort
# does poorly, and reasoning tokens bill against the same cap as the JSON. A
# judgment truncated by the cap is discarded as an error rather than guessed
# at, so the cap sits well above the few dozen tokens the schema needs.
JUDGE_REASONING_EFFORT = "low"
JUDGE_MAX_OUTPUT_TOKENS = 800

JUDGE_SYSTEM = """\
You grade one reply from an antibody validation assistant against an authored ideal answer.

The ideal is the only standard of correctness. It was written by the team that owns the
subject matter, and it defines what a good reply to this question contains. Never grade
against your own knowledge of the topic: do not reward substance the ideal does not
contain, and do not penalize the reply for leaving out something the ideal also leaves
out. If you believe the ideal is wrong, grade against it anyway.

Answer two questions independently.

covers_ideal: does the reply carry the substance of the ideal? True when a reader would
come away with the ideal's main points. Minor omissions of detail are acceptable, missing
the ideal's central claim or its stated caveat is not.

contradicts_ideal: does the reply state anything the ideal contradicts? True only for a
real conflict of fact or emphasis, not for extra material the ideal is silent about.

Judge substance only. Ignore differences of wording, ordering, length, tone, and
formatting, ignore bracketed citation markers such as [what-is-an-antibody], and ignore
whether the reply ends with a question. Those properties are checked elsewhere.

Keep the rationale to one sentence naming the specific point that decided the grade."""

JUDGE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "judgment",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "covers_ideal": {
                    "type": "boolean",
                    "description": "The reply carries the substance of the ideal.",
                },
                "contradicts_ideal": {
                    "type": "boolean",
                    "description": "The reply states something the ideal contradicts.",
                },
                "rationale": {
                    "type": "string",
                    "description": "One sentence naming the point that decided the grade.",
                },
            },
            "required": ["covers_ideal", "contradicts_ideal", "rationale"],
            "additionalProperties": False,
        },
    },
}

USER_TEMPLATE = """Question:
{question}

Authored ideal:
{ideal}

Reply to grade:
{reply}"""


def build_judge_messages(case: dict, reply: str) -> list[dict]:
    """Render the grading prompt for one case and one reply.

    Pure and deterministic, so the same case and reply always produce the same
    messages. The eval's cache key is taken over this list, which is what makes
    a rubric edit invalidate every stored judgment.
    """
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {
            "role": "user",
            "content": USER_TEMPLATE.format(
                question=case["question"],
                ideal=case["ideal"].rstrip(),
                reply=reply,
            ),
        },
    ]


def _judge_error(model: str, reason: str) -> dict:
    """Report a judgment that could not be obtained, without raising."""
    return {"model": model, "error": reason}


def judge_reply(client, model: str, case: dict, reply: str) -> dict:
    """Grade one reply against its case's ideal with one call.

    Returns either a verdict dict or an error dict, and never raises, because
    the caller is a scoring loop that has already spent money on the replies
    being scored. The verdict is derived from the two booleans rather than
    asked for directly, so a judge cannot pass a reply it has just said
    contradicts the ideal.
    """
    from openai import OpenAIError

    try:
        response = client.chat.completions.create(
            model=model,
            messages=build_judge_messages(case, reply),
            reasoning_effort=JUDGE_REASONING_EFFORT,
            max_completion_tokens=JUDGE_MAX_OUTPUT_TOKENS,
            response_format=JUDGE_SCHEMA,
        )
    except OpenAIError as exc:
        return _judge_error(model, f"api_error: {type(exc).__name__}")

    choice = response.choices[0]
    if choice.finish_reason == "length":
        return _judge_error(model, "length")
    try:
        parsed = json.loads(choice.message.content)
    except (TypeError, json.JSONDecodeError):
        return _judge_error(model, "bad_json")
    if not isinstance(parsed, dict):
        return _judge_error(model, "bad_json")

    covers = parsed.get("covers_ideal")
    contradicts = parsed.get("contradicts_ideal")
    rationale = parsed.get("rationale")
    if not isinstance(covers, bool) or not isinstance(contradicts, bool):
        return _judge_error(model, "bad_fields")
    if not isinstance(rationale, str):
        return _judge_error(model, "bad_fields")
    return {
        "model": model,
        "verdict": "pass" if covers and not contradicts else "fail",
        "rationale": rationale.strip(),
        "covers_ideal": covers,
        "contradicts_ideal": contradicts,
    }
