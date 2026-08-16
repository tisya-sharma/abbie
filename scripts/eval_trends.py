#!/usr/bin/env python3
"""Per-check pass rates across recorded eval runs.

Every results file already stores each check's outcome for every case, and
nothing read it as a series. At this golden-set size a moving pass rate is not a
finding on its own, because resampling alone shifts it by a case or two. A single
check degrading across several runs is a finding, and that is what this prints.

Reads only what is on disk, so it costs nothing and needs no API key:

    python3 scripts/eval_trends.py
    python3 scripts/eval_trends.py --config routed --last 6
    python3 scripts/eval_trends.py --check max_em_dashes
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1] / "packages" / "eval" / "results"


def load_runs(config: str | None, model: str | None) -> list[dict]:
    """Every matching run block on disk, oldest first, tagged with its file."""
    runs = []
    for path in sorted(RESULTS.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for run in payload.get("runs", []):
            if config and run.get("config") != config:
                continue
            if model and run.get("model") != model:
                continue
            runs.append(
                {
                    "run_id": payload.get("run_id", path.stem),
                    "commit": (payload.get("git") or {}).get("commit", "?")[:7],
                    "cases": run.get("cases", []),
                    "summary": run.get("summary", {}),
                }
            )
    return runs


def check_rates(cases: list[dict]) -> dict[str, tuple[int, int]]:
    """Passed and total per check name, over the cases where it applies.

    A check absent from a case did not fail there, it was not asked, so the
    denominator is per check rather than the case count.
    """
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for case in cases:
        for name, ok in (case.get("checks") or {}).items():
            tally[name][1] += 1
            tally[name][0] += bool(ok)
    return {name: (passed, total) for name, (passed, total) in tally.items()}


def sparkline(values: list[float | None]) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    return "".join(
        "·" if v is None else blocks[min(int(v * len(blocks)), len(blocks) - 1)]
        for v in values
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="routed")
    parser.add_argument("--model", default=None)
    parser.add_argument("--last", type=int, default=8, help="runs to show")
    parser.add_argument("--check", default=None, help="one check, per-case detail")
    args = parser.parse_args()

    runs = load_runs(args.config, args.model)[-args.last :]
    if not runs:
        print(f"no recorded runs for config {args.config!r} in {RESULTS}")
        return 1

    print(f"{len(runs)} runs, config {args.config}, oldest first\n")
    for run in runs:
        summary = run["summary"]
        cases = len(run["cases"])
        print(
            f"  {run['run_id']}  {run['commit']}  "
            f"{summary.get('passed', '?')}/{cases} cases"
        )

    if args.check:
        print(f"\nper-case history for {args.check}\n")
        history: dict[str, list[str]] = defaultdict(list)
        for run in runs:
            seen = set()
            for case in run["cases"]:
                checks = case.get("checks") or {}
                if args.check in checks:
                    history[case["id"]].append("." if checks[args.check] else "X")
                    seen.add(case["id"])
            for cid in history:
                if cid not in seen:
                    history[cid].append(" ")
        for cid, marks in sorted(history.items(), key=lambda kv: -kv[1].count("X")):
            if "X" in marks:
                print(f"  {''.join(marks):<10} {cid}")
        return 0

    series: dict[str, list[float | None]] = defaultdict(list)
    for run in runs:
        rates = check_rates(run["cases"])
        for name in set(series) | set(rates):
            passed, total = rates.get(name, (0, 0))
            series[name].append(passed / total if total else None)

    print(f"\n{'check':<24} {'trend':<10} {'latest':>8}   n")
    print("  " + "-" * 52)
    latest = {n: v[-1] for n, v in series.items()}
    for name in sorted(series, key=lambda n: (latest[n] is None, latest[n])):
        values = series[name]
        last = latest[name]
        total = check_rates(runs[-1]["cases"]).get(name, (0, 0))[1]
        shown = "     n/a" if last is None else f"{last:>7.1%}"
        print(f"  {name:<24} {sparkline(values):<10} {shown}   {total}")

    print(
        "\nA check flat at 100% across runs is a candidate for a blocking gate tier."
        "\nOne drifting down is the thing worth reading; the headline pass rate at"
        "\nthis sample size moves on resampling alone."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
