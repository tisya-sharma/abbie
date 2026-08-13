"""Token pricing, shared by the eval harness and runtime telemetry.

Kept in one place so a cost figure in a production trace and a cost figure in
an eval report are computed the same way. Two consumers disagreeing about what
a turn cost is worse than either being slightly stale.
"""

from __future__ import annotations

# USD per million input/output tokens, checked against published rates 2026-08-11.
# Reasoning tokens bill as output. Unknown models report cost as null, never a guess.
PRICING = {
    "gpt-5-mini": (0.125, 1.00),
    "gpt-5": (0.625, 5.00),
}


def estimate_cost(
    model: str, prompt_tokens: int, completion_tokens: int
) -> float | None:
    """USD for one call, or None when the model's rates are not known.

    None rather than zero: a missing price is missing information, and summing
    it as zero would quietly understate a run's total.
    """
    if model not in PRICING:
        return None
    input_rate, output_rate = PRICING[model]
    return round(
        (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000, 6
    )
