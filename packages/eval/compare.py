#!/usr/bin/env python3
"""Paired comparison of two recorded eval runs with an exact McNemar test.

Pass counts on a small golden set cannot distinguish improvement from
sampling noise; the correct reading is per-case paired flips between the two
runs, tested with the exact binomial McNemar on the discordant pairs. This
tool computes that from the results JSON the runner already writes.

Usage:
    python3 packages/eval/compare.py results/eval-A.json results/eval-B.json
    python3 packages/eval/compare.py A.json B.json --model gpt-5-mini --a-config full-context --b-config routed
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def select_run(payload: dict, model: str | None, config: str | None, label: str) -> dict:
    """Pick exactly one run block from a results file, or exit with the options."""
    runs = payload["runs"]
    matches = [
        r for r in runs
        if (model is None or r["model"] == model)
        and (config is None or r["config"] == config)
    ]
    if len(matches) == 1:
        return matches[0]
    options = ", ".join(f"{r['model']}/{r['config']}" for r in runs)
    raise SystemExit(
        f"{label}: expected exactly one matching run, found {len(matches)}. "
        f"Available: {options}. Narrow with --model / --{label}-config."
    )


def exact_mcnemar(b: int, c: int) -> float:
    """Two-sided exact binomial McNemar p-value on discordant pair counts.

    b and c are the two flip directions. Under the null both are equally
    likely, so the p-value is the two-sided binomial tail at min(b, c).
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired eval-run comparison")
    parser.add_argument("run_a", help="results JSON for the baseline side")
    parser.add_argument("run_b", help="results JSON for the candidate side")
    parser.add_argument("--model", help="restrict both sides to this model")
    parser.add_argument("--a-config", help="config name to select in run A")
    parser.add_argument("--b-config", help="config name to select in run B")
    args = parser.parse_args()

    payload_a = json.loads(Path(args.run_a).read_text(encoding="utf-8"))
    payload_b = json.loads(Path(args.run_b).read_text(encoding="utf-8"))
    run_a = select_run(payload_a, args.model, args.a_config, "a")
    run_b = select_run(payload_b, args.model, args.b_config, "b")

    verdicts_a = {c["id"]: c["passed"] for c in run_a["cases"]}
    verdicts_b = {c["id"]: c["passed"] for c in run_b["cases"]}
    shared = sorted(set(verdicts_a) & set(verdicts_b))
    only_one_side = sorted(set(verdicts_a) ^ set(verdicts_b))
    if only_one_side:
        print(f"ignoring {len(only_one_side)} case(s) present on one side only: "
              + ", ".join(only_one_side))
    if not shared:
        raise SystemExit("no shared cases to compare")

    gained = [cid for cid in shared if not verdicts_a[cid] and verdicts_b[cid]]
    lost = [cid for cid in shared if verdicts_a[cid] and not verdicts_b[cid]]
    p = exact_mcnemar(len(gained), len(lost))

    label_a = f"{run_a['model']}/{run_a['config']} ({payload_a.get('run_id', '?')})"
    label_b = f"{run_b['model']}/{run_b['config']} ({payload_b.get('run_id', '?')})"
    print(f"A: {label_a}  {sum(verdicts_a[c] for c in shared)}/{len(shared)}")
    print(f"B: {label_b}  {sum(verdicts_b[c] for c in shared)}/{len(shared)}")
    for cid in gained:
        print(f"  fail -> pass  {cid}")
    for cid in lost:
        print(f"  pass -> fail  {cid}")
    if not gained and not lost:
        print("  no discordant cases")

    print(f"\nflips: +{len(gained)}/-{len(lost)}, exact McNemar p = {p:.3f}")
    if p < 0.05:
        print("verdict: statistically distinguishable at the 5% level")
    else:
        print(
            "verdict: not statistically distinguishable from noise at this set size; "
            "certify the change structurally, or add repeats and cases before deciding"
        )


if __name__ == "__main__":
    main()
