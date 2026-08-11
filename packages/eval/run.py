#!/usr/bin/env python3
"""Run the golden evaluation set against one or more models and configurations.

Every run writes a timestamped JSON record plus a markdown report to
packages/eval/results/, keyed to the git commit, because a baseline cannot be
reconstructed after the fact. The per-case diff table in the report is the
model-attribution view: a failure that persists on the capable tier points at
the system or corpus, a failure only on the cheap tier points at the model.

Usage:
    python3 packages/eval/run.py --dry-run
    python3 packages/eval/run.py --configs full-context
    python3 packages/eval/run.py --models gpt-5-mini,gpt-5 --configs full-context
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import yaml

from packages.corpus_loader import build_system_message, estimate_tokens
from packages.envfile import load_env_file
from packages.eval.checks import score_case

load_env_file()

GOLDEN_PATH = REPO_ROOT / "packages" / "eval" / "golden.yaml"
SYSTEM_PROMPT_PATH = REPO_ROOT / "apps" / "api" / "prompts" / "system.md"
RESULTS_DIR = REPO_ROOT / "packages" / "eval" / "results"
DEFAULT_MODEL = os.environ.get("ABBIE_MODEL", "gpt-5-mini")

# USD per million input/output tokens, checked against published rates 2026-08-11.
# Reasoning tokens bill as output. Unknown models report cost as null, never a guess.
PRICING = {
    "gpt-5-mini": (0.125, 1.00),
    "gpt-5": (0.625, 5.00),
}

DRY_RUN_OUTPUT_GUESS = 800


def load_golden() -> tuple[dict[str, list], list[dict]]:
    """Parse golden.yaml into the property-check spec and the case list."""
    data = yaml.safe_load(GOLDEN_PATH.read_text(encoding="utf-8"))
    return data["property_checks"], data["cases"]


def build_configs(names: list[str]) -> tuple[dict[str, str], dict]:
    """Assemble the requested system messages from the shared prompt pipeline.

    naive is the bare prompt with no corpus, the floor every other
    configuration has to beat. full-context is exactly what the CLI serves.
    """
    prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    full_context, concepts = build_system_message(prompt)
    available = {"naive": prompt, "full-context": full_context}
    unknown = [n for n in names if n not in available]
    if unknown:
        raise SystemExit(
            f"unknown config(s) {', '.join(unknown)}: retrieval is not built yet, "
            "available configs are naive and full-context"
        )
    return {name: available[name] for name in names}, concepts


def git_state() -> dict:
    """Record which commit this run measures, and whether the tree was dirty."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip())
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "no-commits", "dirty": True}


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile, adequate for a handful of latency samples."""
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(p / 100 * (len(ordered) - 1))))
    return ordered[index]


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    """Dollar cost of one call, or None when the model is not in the table."""
    if model not in PRICING:
        return None
    input_rate, output_rate = PRICING[model]
    return round(
        (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000, 6
    )


def ask(
    client,
    model: str,
    system: str,
    question: str,
    max_output_tokens: int,
    reasoning_effort: str,
) -> dict:
    """One non-streaming completion, returning the reply plus measurements.

    Reasoning effort is pinned rather than left to the model default because
    reasoning tokens bill as output and count against the completion cap; at
    the default effort they can consume the entire cap and return an empty
    reply. Every run records the value used, since it changes behavior.
    """
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
        max_completion_tokens=max_output_tokens,
        reasoning_effort=reasoning_effort,
    )
    latency_ms = round((time.perf_counter() - start) * 1000)
    choice = response.choices[0]
    usage = response.usage
    details = getattr(usage, "completion_tokens_details", None)
    return {
        "reply": choice.message.content or "",
        "finish_reason": choice.finish_reason,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "reasoning_tokens": getattr(details, "reasoning_tokens", 0) or 0,
        "latency_ms": latency_ms,
    }


def summarize(cases: list[dict]) -> dict:
    """Aggregate one model-config block, grouped so the naive floor stays legible."""
    answer_cases = [c for c in cases if c["behavior_expected"] == "answer"]
    voice_checks = [
        passed
        for c in answer_cases
        for name, passed in c["checks"].items()
        if name not in ("behavior", "must_cite")
    ]
    latencies = [c["latency_ms"] for c in cases]
    costs = [c["cost_usd"] for c in cases if c["cost_usd"] is not None]
    return {
        "passed": sum(1 for c in cases if c["passed"]),
        "failed": sum(1 for c in cases if not c["passed"]),
        "behavior_accuracy": round(
            sum(c["checks"]["behavior"] for c in cases) / len(cases), 3
        ),
        "citation_pass_rate": round(
            sum(c["checks"]["must_cite"] for c in answer_cases) / len(answer_cases), 3
        ) if answer_cases else None,
        "voice_pass_rate": round(
            sum(voice_checks) / len(voice_checks), 3
        ) if voice_checks else None,
        "latency_ms": {"p50": percentile(latencies, 50), "p95": percentile(latencies, 95)},
        "tokens": {
            "prompt": sum(c["prompt_tokens"] for c in cases),
            "completion": sum(c["completion_tokens"] for c in cases),
        },
        "cost_usd": round(sum(costs), 4) if costs else None,
    }


def run_matrix(
    client,
    models: list[str],
    configs: dict[str, str],
    cases: list[dict],
    property_spec: dict,
    concepts: dict,
    max_output_tokens: int,
    reasoning_effort: str,
) -> list[dict]:
    """Score every model x config x case combination, printing progress."""
    runs = []
    for model in models:
        for config_name, system in configs.items():
            print(f"running {model} / {config_name} ({len(cases)} cases)")
            scored = []
            for case in cases:
                measured = ask(
                    client, model, system, case["question"],
                    max_output_tokens, reasoning_effort,
                )
                result = score_case(case, measured["reply"], concepts, property_spec)
                if measured["finish_reason"] == "length":
                    result["failures"].append("infrastructure: hit max_completion_tokens")
                    result["passed"] = False
                result.update(
                    finish_reason=measured["finish_reason"],
                    prompt_tokens=measured["prompt_tokens"],
                    completion_tokens=measured["completion_tokens"],
                    reasoning_tokens=measured["reasoning_tokens"],
                    latency_ms=measured["latency_ms"],
                    cost_usd=estimate_cost(
                        model, measured["prompt_tokens"], measured["completion_tokens"]
                    ),
                    reply=measured["reply"],
                )
                scored.append(result)
                marker = "pass" if result["passed"] else "FAIL"
                print(f"  {case['id']:34} {marker}")
            runs.append(
                {
                    "config": config_name,
                    "model": model,
                    "system_tokens_estimate": estimate_tokens(configs[config_name]),
                    "cases": scored,
                    "summary": summarize(scored),
                }
            )
    return runs


def write_results(payload: dict) -> Path:
    """Persist the full run record as JSON and return its path."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"eval-{payload['run_id']}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_report(payload: dict, cases: list[dict]) -> Path:
    """Render the human-review report: diff table first, then replies beside ideals."""
    runs = payload["runs"]
    columns = [f"{r['model']} / {r['config']}" for r in runs]
    lines = [
        f"# Eval report {payload['run_id']}",
        "",
        f"Commit {payload['git']['commit']}"
        + (" (dirty)" if payload["git"]["dirty"] else ""),
        "",
        "| case | " + " | ".join(columns) + " |",
        "|---|" + "---|" * len(columns),
    ]
    for case in cases:
        row = [case["id"]]
        for run in runs:
            scored = next(c for c in run["cases"] if c["id"] == case["id"])
            row.append("pass" if scored["passed"] else "; ".join(scored["failures"]))
        lines.append("| " + " | ".join(row) + " |")

    for case in cases:
        lines += ["", f"## {case['id']}", "", f"**Question.** {case['question']}"]
        for run in runs:
            scored = next(c for c in run["cases"] if c["id"] == case["id"])
            lines += ["", f"**{run['model']} / {run['config']}**", "", scored["reply"]]
        lines += ["", "**Golden ideal**", "", case["ideal"].rstrip()]

    path = RESULTS_DIR / f"eval-{payload['run_id']}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def dry_run(models: list[str], configs: dict[str, str], cases: list[dict]) -> None:
    """Print the run matrix and a cost projection without any API calls."""
    print(f"{len(cases)} cases x {len(configs)} config(s) x {len(models)} model(s)")
    for model in models:
        for name, system in configs.items():
            system_tokens = estimate_tokens(system)
            prompt_total = sum(
                system_tokens + estimate_tokens(c["question"]) for c in cases
            )
            completion_total = DRY_RUN_OUTPUT_GUESS * len(cases)
            cost = estimate_cost(model, prompt_total, completion_total)
            cost_text = f"~${cost:.3f}" if cost is not None else "unknown (model not in pricing table)"
            print(
                f"  {model} / {name}: ~{prompt_total} prompt tokens, "
                f"~{completion_total} completion tokens, {cost_text}"
            )
    print("no API calls made")


def main() -> None:
    parser = argparse.ArgumentParser(description="Golden-set eval runner")
    parser.add_argument("--models", default=DEFAULT_MODEL,
                        help="comma-separated model list")
    parser.add_argument("--configs", default="naive,full-context",
                        help="comma-separated subset of: naive, full-context")
    parser.add_argument("--case", action="append",
                        help="run only this case id, repeatable")
    parser.add_argument("--max-output-tokens", type=int, default=4096,
                        help="cap per reply, reasoning tokens count against it")
    parser.add_argument("--reasoning-effort", default="low",
                        choices=["minimal", "low", "medium", "high"],
                        help="reasoning effort passed to the model, recorded in results")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the matrix and cost projection, no API calls")
    parser.add_argument("--no-report", action="store_true",
                        help="skip the markdown report")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    try:
        configs, concepts = build_configs(
            [c.strip() for c in args.configs.split(",") if c.strip()]
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    property_spec, cases = load_golden()
    if args.case:
        unknown = set(args.case) - {c["id"] for c in cases}
        if unknown:
            raise SystemExit(f"unknown case id(s): {', '.join(sorted(unknown))}")
        cases = [c for c in cases if c["id"] in args.case]

    if args.dry_run:
        dry_run(models, configs, cases)
        return

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Paste IPI's key into .env at the repo root,"
            " or export it in this shell."
        )

    from openai import OpenAI

    client = OpenAI()
    runs = run_matrix(
        client, models, configs, cases, property_spec, concepts,
        args.max_output_tokens, args.reasoning_effort,
    )

    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "schema_version": 1,
        "run_id": now.strftime("%Y%m%d-%H%M%S"),
        "timestamp_utc": now.isoformat(timespec="seconds"),
        "git": git_state(),
        "invocation": {
            "models": models,
            "configs": list(configs),
            "max_output_tokens": args.max_output_tokens,
            "reasoning_effort": args.reasoning_effort,
        },
        "runs": runs,
    }
    results_path = write_results(payload)
    print(f"\nresults: {results_path.relative_to(REPO_ROOT)}")
    if not args.no_report:
        report_path = write_report(payload, cases)
        print(f"report:  {report_path.relative_to(REPO_ROOT)}")

    for run in runs:
        s = run["summary"]
        cost_text = f"${s['cost_usd']}" if s["cost_usd"] is not None else "cost unknown"
        print(
            f"{run['model']} / {run['config']}: {s['passed']} passed, {s['failed']} failed, "
            f"p50 {s['latency_ms']['p50']}ms, {cost_text}"
        )


if __name__ == "__main__":
    main()
