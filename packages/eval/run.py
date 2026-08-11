#!/usr/bin/env python3
"""Run the golden evaluation set against one or more models and configurations.

Every run writes a timestamped JSON record plus a markdown report to
packages/eval/results/, keyed to the git commit, because a baseline cannot be
reconstructed after the fact. The per-case diff table in the report is the
model-attribution view: a failure that persists on the capable tier points at
the system or corpus, a failure only on the cheap tier points at the model.
The routed configuration adds the behavior router in front of composition and
must beat full-context on the same set before it merges.

Usage:
    python3 packages/eval/run.py --dry-run
    python3 packages/eval/run.py --configs full-context
    python3 packages/eval/run.py --models gpt-5-mini,gpt-5 --configs full-context,routed
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import yaml

from packages.composer import ComposerPrompts, read_prompt_file, respond
from packages.corpus_loader import build_system_message, estimate_tokens
from packages.envfile import load_env_file
from packages.eval.checks import score_case
from packages.router import classify

load_env_file()

GOLDEN_PATH = REPO_ROOT / "packages" / "eval" / "golden.yaml"
PROMPTS_DIR = REPO_ROOT / "apps" / "api" / "prompts"
RESULTS_DIR = REPO_ROOT / "packages" / "eval" / "results"
CACHE_DIR = REPO_ROOT / "packages" / "eval" / ".cache"
DEFAULT_MODEL = os.environ.get("ABBIE_MODEL", "gpt-5-mini")
DEFAULT_ROUTER_MODEL = os.environ.get("ABBIE_ROUTER_MODEL", "gpt-5-mini")

# USD per million input/output tokens, checked against published rates 2026-08-11.
# Reasoning tokens bill as output. Unknown models report cost as null, never a guess.
PRICING = {
    "gpt-5-mini": (0.125, 1.00),
    "gpt-5": (0.625, 5.00),
}

DRY_RUN_OUTPUT_GUESS = 800
DRY_RUN_ROUTER_OUTPUT_GUESS = 40

ROUTER_RESULT_KEYS = (
    "router_behavior",
    "router_subject",
    "router_fallback",
    "router_model",
    "router_prompt_tokens",
    "router_completion_tokens",
    "router_latency_ms",
)


def load_golden() -> tuple[dict[str, list], list[dict]]:
    """Parse golden.yaml into the property-check spec and the case list."""
    data = yaml.safe_load(GOLDEN_PATH.read_text(encoding="utf-8"))
    return data["property_checks"], data["cases"]


def _text_hash(text: str) -> str:
    """Short stable digest used in cache keys and strategy fingerprints."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def cache_key(fingerprint: str, model: str, question: str, reasoning_effort: str,
              max_output_tokens: int, trial: int) -> str:
    """Key one sampled call. Trial-aware so repeats stay independent samples.

    The cache exists for resumability and free reruns of unchanged
    configurations, never to deduplicate the samples a variance estimate
    depends on — each trial index is its own cache entry.
    """
    payload = json.dumps(
        [fingerprint, model, question, reasoning_effort, max_output_tokens, trial]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def cache_get(key: str) -> dict | None:
    """Return a cached measurement, or None on miss or unreadable entry."""
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def cache_put(key: str, measured: dict) -> None:
    """Store one measurement for reuse by identical future calls."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{key}.json").write_text(
        json.dumps(measured), encoding="utf-8"
    )


class SingleCallStrategy:
    """One full system message per case: the naive and full-context configs."""

    def __init__(self, name: str, system: str):
        self.name = name
        self.system_tokens_estimate = estimate_tokens(system)
        self.fingerprint = _text_hash(system)
        self._system = system

    def run_case(self, client, model, question, max_output_tokens, reasoning_effort):
        """Measure one single-call turn."""
        return ask(client, model, self._system, question, max_output_tokens, reasoning_effort)

    def dry_run_tokens(self, cases: list[dict]) -> tuple[int, int]:
        """Projected prompt and completion tokens for one model pass."""
        prompt_total = sum(
            self.system_tokens_estimate + estimate_tokens(c["question"]) for c in cases
        )
        return prompt_total, DRY_RUN_OUTPUT_GUESS * len(cases)


class RoutedStrategy:
    """Behavior router plus per-behavior composition: the routed config."""

    def __init__(self, name: str, prompts: ComposerPrompts, router_prompt: str, router_model: str):
        self.name = name
        self.system_tokens_estimate = estimate_tokens(prompts.answer_system)
        self.fingerprint = _text_hash(
            prompts.answer_system + prompts.redirect_system + prompts.refuse_text
            + prompts.abstain_template + router_prompt + router_model
        )
        self._prompts = prompts
        self._router_prompt = router_prompt
        self._router_tokens = estimate_tokens(router_prompt)
        self._router_model = router_model

    def run_case(self, client, model, question, max_output_tokens, reasoning_effort):
        """Measure one routed turn: classify, then compose per behavior."""
        route = classify(client, question, self._router_model, self._router_prompt)
        result = respond(
            client, route, question, self._prompts, model,
            reasoning_effort, max_output_tokens=max_output_tokens,
        )
        return {
            "reply": result.text,
            "finish_reason": result.finish_reason,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "reasoning_tokens": result.reasoning_tokens,
            "latency_ms": result.latency_ms + route.latency_ms,
            "router_behavior": route.behavior,
            "router_subject": route.subject,
            "router_fallback": route.fallback,
            "router_model": route.model,
            "router_prompt_tokens": route.prompt_tokens,
            "router_completion_tokens": route.completion_tokens,
            "router_latency_ms": route.latency_ms,
        }

    def dry_run_tokens(self, cases: list[dict]) -> tuple[int, int]:
        """Worst-case projection: every case routes to the full answer path."""
        prompt_total = sum(
            self.system_tokens_estimate
            + self._router_tokens
            + 2 * estimate_tokens(c["question"])
            for c in cases
        )
        completion_total = (DRY_RUN_OUTPUT_GUESS + DRY_RUN_ROUTER_OUTPUT_GUESS) * len(cases)
        return prompt_total, completion_total


def build_strategies(names: list[str], router_model: str) -> tuple[list, dict]:
    """Assemble the requested configurations from the shared prompt pipeline.

    naive is the bare prompt with no corpus, the floor every other
    configuration has to beat. full-context is exactly what the baseline CLI
    serves. routed is the router-plus-composer pipeline. retrieval does not
    exist yet and is rejected by name.
    """
    prompt = read_prompt_file(PROMPTS_DIR / "system.md")
    full_context, concepts = build_system_message(prompt)
    strategies: list = []
    for name in names:
        if name == "naive":
            strategies.append(SingleCallStrategy("naive", prompt))
        elif name == "full-context":
            strategies.append(SingleCallStrategy("full-context", full_context))
        elif name == "routed":
            prompts = ComposerPrompts(
                answer_system=full_context,
                redirect_system=read_prompt_file(PROMPTS_DIR / "redirect.md"),
                refuse_text=read_prompt_file(PROMPTS_DIR / "refuse.md"),
                abstain_template=read_prompt_file(PROMPTS_DIR / "abstain.md"),
            )
            router_prompt = read_prompt_file(PROMPTS_DIR / "router.md")
            strategies.append(RoutedStrategy("routed", prompts, router_prompt, router_model))
        else:
            raise SystemExit(
                f"unknown config {name!r}: retrieval is not built yet, "
                "available configs are naive, full-context, and routed"
            )
    return strategies, concepts


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


def case_cost(model: str, measured: dict) -> float | None:
    """Fold composer and router costs for one case, null if either is unknown."""
    cost = estimate_cost(model, measured["prompt_tokens"], measured["completion_tokens"])
    if "router_behavior" not in measured:
        return cost
    router_cost = estimate_cost(
        measured["router_model"],
        measured["router_prompt_tokens"],
        measured["router_completion_tokens"],
    )
    if cost is None or router_cost is None:
        return None
    return round(cost + router_cost, 6)


def ask(client, model: str, system: str, question: str, max_output_tokens: int,
        reasoning_effort: str) -> dict:
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
    n = len(cases)
    passed = sum(1 for c in cases if c["passed"])
    pass_rate = passed / n
    summary = {
        "passed": passed,
        "failed": n - passed,
        "unstable": sum(1 for c in cases if c.get("unstable")),
        "pass_rate": round(pass_rate, 3),
        "pass_rate_se": round((pass_rate * (1 - pass_rate) / n) ** 0.5, 3),
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
            "prompt": sum(
                c["prompt_tokens"] + c.get("router_prompt_tokens", 0) for c in cases
            ),
            "completion": sum(
                c["completion_tokens"] + c.get("router_completion_tokens", 0)
                for c in cases
            ),
        },
        "cost_usd": round(sum(costs), 4) if costs else None,
    }
    routed = [c for c in cases if "router_behavior" in c]
    if routed:
        summary["router"] = {
            "accuracy": round(
                sum(c["router_behavior"] == c["behavior_expected"] for c in routed)
                / len(routed), 3,
            ),
            "fallbacks": sum(1 for c in routed if c.get("router_fallback")),
        }
    return summary


def score_trial(case: dict, measured: dict, model: str, concepts: dict,
                property_spec: dict) -> dict:
    """Score one measured trial and fold in its measurements."""
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
        cost_usd=case_cost(model, measured),
        reply=measured["reply"],
        cached=measured.get("cached", False),
    )
    for key in ROUTER_RESULT_KEYS:
        if key in measured:
            result[key] = measured[key]
    return result


def _fold_failures(trials: list[dict], n: int) -> list[str]:
    """Merge trial failure lists, annotating each with its trial frequency."""
    counts: dict[str, int] = {}
    for t in trials:
        for f in t["failures"]:
            counts[f] = counts.get(f, 0) + 1
    return [
        f if n == 1 else f"{f} [{count}/{n} trials]"
        for f, count in sorted(counts.items(), key=lambda kv: -kv[1])
    ]


def aggregate_trials(case: dict, trials: list[dict]) -> dict:
    """Fold N scored trials into one case record with a majority verdict.

    A case is unstable when trials disagree; unstable cases fail unless a
    strict majority passed, and the mixed outcome is visible either way.
    Tokens and cost sum across trials because they were really spent; latency
    reports the median trial.
    """
    n = len(trials)
    passes = sum(1 for t in trials if t["passed"])
    failures = _fold_failures(trials, n)
    costs = [t["cost_usd"] for t in trials if t["cost_usd"] is not None]
    record = {
        "id": case["id"],
        "behavior_expected": case["behavior"],
        "behavior_observed": trials[0]["behavior_observed"],
        "citations": trials[0]["citations"],
        "checks": trials[0]["checks"],
        "passed": passes > n / 2,
        "unstable": 0 < passes < n,
        "pass_fraction": round(passes / n, 3),
        "trial_count": n,
        "failures": failures,
        "prompt_tokens": sum(t["prompt_tokens"] for t in trials),
        "completion_tokens": sum(t["completion_tokens"] for t in trials),
        "reasoning_tokens": sum(t["reasoning_tokens"] for t in trials),
        "latency_ms": round(statistics.median(t["latency_ms"] for t in trials)),
        "cost_usd": round(sum(costs), 6) if costs else None,
        "reply": trials[0]["reply"],
        "judge": None,
    }
    for key in ROUTER_RESULT_KEYS:
        if key in trials[0]:
            record[key] = trials[0][key]
    if n > 1:
        record["trials"] = [
            {k: t[k] for k in ("passed", "failures", "behavior_observed",
                               "citations", "reply", "latency_ms", "cached")}
            for t in trials
        ]
    return record


def run_matrix(
    client,
    models: list[str],
    strategies: list,
    cases: list[dict],
    property_spec: dict,
    concepts: dict,
    max_output_tokens: int,
    reasoning_effort: str,
    repeats: int,
    use_cache: bool,
) -> list[dict]:
    """Score every model x config x case x trial combination, printing progress."""
    runs = []
    for model in models:
        for strategy in strategies:
            print(f"running {model} / {strategy.name} ({len(cases)} cases x {repeats} trial(s))")
            scored = []
            for case in cases:
                trials = []
                for trial in range(repeats):
                    key = cache_key(
                        strategy.fingerprint, model, case["question"],
                        reasoning_effort, max_output_tokens, trial,
                    )
                    measured = cache_get(key) if use_cache else None
                    if measured is None:
                        measured = strategy.run_case(
                            client, model, case["question"],
                            max_output_tokens, reasoning_effort,
                        )
                        if use_cache:
                            cache_put(key, measured)
                        measured["cached"] = False
                    else:
                        measured["cached"] = True
                    trials.append(
                        score_trial(case, measured, model, concepts, property_spec)
                    )
                record = aggregate_trials(case, trials)
                scored.append(record)
                if record["unstable"]:
                    marker = f"UNSTABLE ({record['pass_fraction']:.0%})"
                else:
                    marker = "pass" if record["passed"] else "FAIL"
                print(f"  {case['id']:34} {marker}")
            runs.append(
                {
                    "config": strategy.name,
                    "model": model,
                    "system_tokens_estimate": strategy.system_tokens_estimate,
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
            scored = next((c for c in run["cases"] if c["id"] == case["id"]), None)
            if scored is None:
                row.append("not run")
            elif scored.get("unstable"):
                row.append(
                    f"unstable {scored['pass_fraction']:.0%}: "
                    + "; ".join(scored["failures"])
                )
            elif scored["passed"]:
                row.append("pass")
            else:
                row.append("; ".join(scored["failures"]))
        lines.append("| " + " | ".join(row) + " |")

    for case in cases:
        lines += ["", f"## {case['id']}", "", f"**Question.** {case['question']}"]
        for run in runs:
            scored = next((c for c in run["cases"] if c["id"] == case["id"]), None)
            if scored is None:
                continue
            trial_note = (
                f" — passed {scored['pass_fraction']:.0%} of {scored['trial_count']} trials"
                if scored.get("trial_count", 1) > 1 else ""
            )
            lines += ["", f"**{run['model']} / {run['config']}**{trial_note}", ""]
            if "router_behavior" in scored:
                subject = (
                    f" (subject: {scored['router_subject']})"
                    if scored.get("router_subject") else ""
                )
                fallback = " [fallback]" if scored.get("router_fallback") else ""
                lines += [f"routed: {scored['router_behavior']}{subject}{fallback}", ""]
            lines += [scored["reply"]]
        lines += ["", "**Golden ideal**", "", case["ideal"].rstrip()]

    path = RESULTS_DIR / f"eval-{payload['run_id']}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def rescore_payload(stored: dict, cases: list[dict], property_spec: dict,
                    concepts: dict) -> dict:
    """Re-run the deterministic checks over a stored run's replies, spending nothing.

    Measurements (tokens, cost, latency) carry over unchanged; only the scoring
    layer is recomputed, which makes scorer iteration free. Cases absent from
    the current golden set are dropped with a notice.
    """
    case_by_id = {c["id"]: c for c in cases}
    for run in stored["runs"]:
        fresh = []
        for old in run["cases"]:
            case = case_by_id.get(old["id"])
            if case is None:
                print(f"  dropping {old['id']}: not in the current golden set")
                continue
            replies = [t["reply"] for t in old.get("trials", [])] or [old["reply"]]
            scores = [score_case(case, r, concepts, property_spec) for r in replies]
            n = len(scores)
            passes = sum(1 for s in scores if s["passed"])
            old.update(
                behavior_observed=scores[0]["behavior_observed"],
                citations=scores[0]["citations"],
                checks=scores[0]["checks"],
                passed=passes > n / 2,
                unstable=0 < passes < n,
                pass_fraction=round(passes / n, 3),
                trial_count=n,
                failures=_fold_failures(scores, n),
            )
            fresh.append(old)
        run["cases"] = fresh
        run["summary"] = summarize(fresh)
    return stored


def dry_run(models: list[str], strategies: list, cases: list[dict], repeats: int) -> None:
    """Print the run matrix and a cost projection without any API calls."""
    print(
        f"{len(cases)} cases x {len(strategies)} config(s) x {len(models)} model(s)"
        f" x {repeats} trial(s)"
    )
    for model in models:
        for strategy in strategies:
            prompt_total, completion_total = strategy.dry_run_tokens(cases)
            prompt_total *= repeats
            completion_total *= repeats
            cost = estimate_cost(model, prompt_total, completion_total)
            cost_text = (
                f"~${cost:.3f}" if cost is not None
                else "unknown (model not in pricing table)"
            )
            print(
                f"  {model} / {strategy.name}: ~{prompt_total} prompt tokens, "
                f"~{completion_total} completion tokens, {cost_text}"
            )
    print("no API calls made")


def main() -> None:
    parser = argparse.ArgumentParser(description="Golden-set eval runner")
    parser.add_argument("--models", default=DEFAULT_MODEL,
                        help="comma-separated model list")
    parser.add_argument("--configs", default="naive,full-context",
                        help="comma-separated subset of: naive, full-context, routed")
    parser.add_argument("--case", action="append",
                        help="run only this case id, repeatable")
    parser.add_argument("--max-output-tokens", type=int, default=4096,
                        help="cap per reply, reasoning tokens count against it")
    parser.add_argument("--reasoning-effort", default="low",
                        choices=["minimal", "low", "medium", "high"],
                        help="reasoning effort for the answer path, recorded in results")
    parser.add_argument("--router-model", default=DEFAULT_ROUTER_MODEL,
                        help="model for the behavior router in the routed config")
    parser.add_argument("--repeats", type=int, default=1,
                        help="trials per case; use 3-5 for decisions at the margin")
    parser.add_argument("--no-cache", action="store_true",
                        help="skip the response cache and draw fresh samples")
    parser.add_argument("--include-holdout", action="store_true",
                        help="include held-out cases; gate runs only, never while tuning")
    parser.add_argument("--rescore", metavar="RESULTS_JSON",
                        help="re-score a stored run's replies with zero API calls")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the matrix and cost projection, no API calls")
    parser.add_argument("--no-report", action="store_true",
                        help="skip the markdown report")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    try:
        strategies, concepts = build_strategies(
            [c.strip() for c in args.configs.split(",") if c.strip()],
            args.router_model,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    property_spec, cases = load_golden()

    if args.rescore:
        stored = json.loads(Path(args.rescore).read_text(encoding="utf-8"))
        stored = rescore_payload(stored, cases, property_spec, concepts)
        original_id = stored.get("run_id", "unknown")
        now = dt.datetime.now(dt.timezone.utc)
        stored["run_id"] = now.strftime("%Y%m%d-%H%M%S")
        stored["timestamp_utc"] = now.isoformat(timespec="seconds")
        stored.setdefault("invocation", {})["rescore_of"] = original_id
        stored["git"] = git_state()
        results_path = write_results(stored)
        print(f"rescored {original_id} with zero API calls")
        print(f"results: {results_path.relative_to(REPO_ROOT)}")
        for run in stored["runs"]:
            s = run["summary"]
            print(f"{run['model']} / {run['config']}: {s['passed']} passed, {s['failed']} failed")
        return

    if not args.include_holdout:
        held_out = [c for c in cases if c.get("holdout")]
        if held_out:
            cases = [c for c in cases if not c.get("holdout")]
            print(
                f"excluding {len(held_out)} holdout case(s); "
                "use --include-holdout for gate runs"
            )

    if args.case:
        unknown = set(args.case) - {c["id"] for c in cases}
        if unknown:
            raise SystemExit(f"unknown case id(s): {', '.join(sorted(unknown))}")
        cases = [c for c in cases if c["id"] in args.case]

    if args.dry_run:
        dry_run(models, strategies, cases, args.repeats)
        return

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Paste IPI's key into .env at the repo root,"
            " or export it in this shell."
        )

    from openai import OpenAI

    client = OpenAI()
    runs = run_matrix(
        client, models, strategies, cases, property_spec, concepts,
        args.max_output_tokens, args.reasoning_effort,
        args.repeats, not args.no_cache,
    )

    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "schema_version": 3,
        "run_id": now.strftime("%Y%m%d-%H%M%S"),
        "timestamp_utc": now.isoformat(timespec="seconds"),
        "git": git_state(),
        "invocation": {
            "models": models,
            "configs": [s.name for s in strategies],
            "max_output_tokens": args.max_output_tokens,
            "reasoning_effort": args.reasoning_effort,
            "router_model": args.router_model,
            "repeats": args.repeats,
            "include_holdout": args.include_holdout,
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
        line = (
            f"{run['model']} / {run['config']}: {s['passed']} passed, "
            f"{s['failed']} failed"
        )
        if s["unstable"]:
            line += f" ({s['unstable']} unstable)"
        line += (
            f", pass rate {s['pass_rate']} +/- {s['pass_rate_se']}, "
            f"p50 {s['latency_ms']['p50']}ms, {cost_text}"
        )
        if "router" in s:
            line += (
                f", router accuracy {s['router']['accuracy']}, "
                f"{s['router']['fallbacks']} fallback(s)"
            )
        print(line)


if __name__ == "__main__":
    main()
