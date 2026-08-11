#!/usr/bin/env python3
"""Interactive Abbie prototype running the full-context baseline.

The whole visible corpus rides in the system prompt, so there is no retrieval
step. Conversation state is the covered set from architecture.md: concept ids
already cited, used to keep follow-up offers fresh.

Usage:
    export OPENAI_API_KEY=...
    python3 apps/cli/chat.py
    python3 apps/cli/chat.py --ask "What is antibody validation?"
    python3 apps/cli/chat.py --internal    includes pre-publication concepts
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from packages.corpus_loader import (
    build_system_message,
    estimate_tokens,
    extract_citations,
)

SYSTEM_PROMPT_PATH = REPO_ROOT / "apps" / "api" / "prompts" / "system.md"
DEFAULT_MODEL = os.environ.get("ABBIE_MODEL", "gpt-5-mini")


def stream_reply(client, model: str, messages: list[dict]) -> str:
    """Stream one completion to stdout and return the full text."""
    stream = client.chat.completions.create(
        model=model, messages=messages, stream=True
    )
    parts: list[str] = []
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        parts.append(delta)
        print(delta, end="", flush=True)
    print()
    return "".join(parts)


def follow_ups_for(cited: list[str], concepts: dict, covered: set[str]) -> list[str]:
    """Graph-derived next topics: leads_to of cited concepts, minus covered."""
    offers: list[str] = []
    for cid in cited:
        for target in concepts[cid].leads_to:
            if target in concepts and target not in covered and target not in offers:
                offers.append(target)
    return offers


def main() -> None:
    parser = argparse.ArgumentParser(description="Abbie full-context baseline")
    parser.add_argument("--ask", help="ask one question and exit")
    parser.add_argument(
        "--internal",
        action="store_true",
        help="include pre-publication concepts (internal build)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Export IPI's key in this shell first."
        )

    from openai import OpenAI

    client = OpenAI()
    prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    try:
        system_message, concepts = build_system_message(prompt, args.internal)
    except ValueError as exc:
        raise SystemExit(f"{exc}\nrefusing to start")

    build = "internal" if args.internal else "public"
    print(
        f"abbie baseline | {build} build | {len(concepts)} concepts | "
        f"~{estimate_tokens(system_message)} tokens of system context | "
        f"model {args.model}\n"
    )

    messages: list[dict] = [{"role": "system", "content": system_message}]
    covered: set[str] = set()

    def turn(question: str) -> None:
        messages.append({"role": "user", "content": question})
        reply = stream_reply(client, args.model, messages)
        messages.append({"role": "assistant", "content": reply})

        cited = extract_citations(reply, concepts)
        covered.update(cited)
        offers = follow_ups_for(cited, concepts, covered)
        if cited:
            print(f"\n  cited: {', '.join(cited)}")
        if offers:
            print(f"  graph follow-ups: {', '.join(offers[:4])}")
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
