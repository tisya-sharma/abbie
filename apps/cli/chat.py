#!/usr/bin/env python3
"""Interactive Abbie prototype with behavior routing.

Each question is classified into one of the four behaviors before any
generation, and each behavior composes its reply from only the context it
needs: answers see the full corpus, redirects see redirect instructions alone,
and refusals and abstentions are deterministic text with no model call.
--baseline skips routing and runs the original single-call full-context
pipeline. Conversation state is the covered set from architecture.md: concept
ids already cited, used to keep follow-up offers fresh.

Usage:
    python3 apps/cli/chat.py
    python3 apps/cli/chat.py --ask "What is antibody validation?"
    python3 apps/cli/chat.py --baseline --ask "Coke or Pepsi?"
    python3 apps/cli/chat.py --internal    includes pre-publication concepts
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from packages.composer import ComposerPrompts, read_prompt_file, respond
from packages.corpus_loader import (
    build_system_message,
    estimate_tokens,
    extract_citations,
)
from packages.envfile import load_env_file
from packages.router import Route, classify

load_env_file()

PROMPTS_DIR = REPO_ROOT / "apps" / "api" / "prompts"
DEFAULT_MODEL = os.environ.get("ABBIE_MODEL", "gpt-5-mini")
DEFAULT_ROUTER_MODEL = os.environ.get("ABBIE_ROUTER_MODEL", "gpt-5-mini")

BASELINE_ROUTE = Route(
    behavior="answer",
    subject=None,
    fallback=False,
    fallback_reason=None,
    model="none",
    prompt_tokens=0,
    completion_tokens=0,
    latency_ms=0,
)


def read_prompt(name: str) -> str:
    """Read one prompt file, failing fast with a clear message if missing."""
    path = PROMPTS_DIR / name
    try:
        return read_prompt_file(path)
    except FileNotFoundError:
        raise SystemExit(f"missing prompt file: {path}")


def follow_ups_for(cited: list[str], concepts: dict, covered: set[str]) -> list[str]:
    """Graph-derived next topics: leads_to of cited concepts, minus covered."""
    offers: list[str] = []
    for cid in cited:
        for target in concepts[cid].leads_to:
            if target in concepts and target not in covered and target not in offers:
                offers.append(target)
    return offers


def main() -> None:
    parser = argparse.ArgumentParser(description="Abbie CLI")
    parser.add_argument("--ask", help="ask one question and exit")
    parser.add_argument(
        "--internal",
        action="store_true",
        help="include pre-publication concepts (internal build)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--reasoning-effort",
        default="low",
        choices=["minimal", "low", "medium", "high"],
        help="reasoning effort for the answer path, low keeps replies fast",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="skip routing and run the original single-call full-context pipeline",
    )
    parser.add_argument(
        "--router-model",
        default=DEFAULT_ROUTER_MODEL,
        help="model for the behavior router",
    )
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Paste IPI's key into .env at the repo root,"
            " or export it in this shell."
        )

    from openai import OpenAI

    client = OpenAI()
    system_prompt = read_prompt("system.md")
    try:
        answer_system, concepts = build_system_message(system_prompt, args.internal)
    except ValueError as exc:
        raise SystemExit(f"{exc}\nrefusing to start")

    if args.baseline:
        router_prompt = ""
        prompts = ComposerPrompts(
            answer_system=answer_system,
            redirect_system="",
            refuse_text="",
            abstain_template="",
        )
    else:
        router_prompt = read_prompt("router.md")
        prompts = ComposerPrompts(
            answer_system=answer_system,
            redirect_system=read_prompt("redirect.md"),
            refuse_text=read_prompt("refuse.md"),
            abstain_template=read_prompt("abstain.md"),
        )

    mode = "baseline" if args.baseline else "routed"
    build = "internal" if args.internal else "public"
    print(
        f"abbie {mode} | {build} build | {len(concepts)} concepts | "
        f"~{estimate_tokens(answer_system)} tokens of system context | "
        f"model {args.model}\n"
    )

    history: list[dict] = []
    covered: set[str] = set()

    def turn(question: str) -> None:
        if args.baseline:
            route = BASELINE_ROUTE
        else:
            route = classify(client, question, args.router_model, router_prompt)
        result = respond(
            client,
            route,
            question,
            prompts,
            args.model,
            args.reasoning_effort,
            history=history,
            on_delta=lambda delta: print(delta, end="", flush=True),
        )
        print()
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": result.text})

        cited = extract_citations(result.text, concepts)
        covered.update(cited)
        offers = follow_ups_for(cited, concepts, covered)
        status: list[str] = []
        if not args.baseline:
            subject = f" (subject: {route.subject})" if route.subject else ""
            fallback = " [router fallback]" if route.fallback else ""
            status.append(f"behavior: {result.behavior}{subject}{fallback}")
        if cited:
            status.append(f"cited: {', '.join(cited)}")
        if offers:
            status.append(f"graph follow-ups: {', '.join(offers[:4])}")
        if status:
            print("\n" + "\n".join(f"  {line}" for line in status))
        print()

    if args.ask:
        turn(args.ask)
        return

    print("Ask Abbie something (ctrl-d or 'exit' to quit).\n")
    while True:
        try:
            question = input("you> ").strip()
        except EOFError:
            print()
            break
        if not question or question.lower() in {"exit", "quit"}:
            break
        turn(question)


if __name__ == "__main__":
    main()
