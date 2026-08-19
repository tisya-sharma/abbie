"""Bounded tool-execution loop for the answer behavior, on LangGraph.

The single composer call is right for explaining a concept and wrong for
carrying a task: "what does IPI have against this target" needs the model to
choose what to fetch. This module is that loop, built as a small StateGraph
from the first shipment rather than hand-rolled now and migrated later.

Its terms are fixed and every one of them is load-bearing:

- the router still runs first and unchanged, so refuse and abstain stay
  deterministic template paths that never enter the loop at all. That is
  enforced structurally: packages.composer dispatches here only after its
  refuse, abstain, and redirect branches have already returned
- tool calls are capped per turn, starting at four. A turn that spends its cap
  returns what it has with the gap stated rather than looping, so the last
  model call runs with no tools offered and a note naming what went unfetched
- every call is a span, so cost and latency stay readable by the feedback loop
- the leak scan runs on the final text exactly as it does now, at the API
  layer, over the text this loop returns. Nothing is scanned or sanitized here,
  because a second scan in a second place is how two policies start to disagree

Transport-free like the tool library it drives: no fastapi, no HTTP, no
knowledge of who called it. The widget calls it in process, and an MCP server
later calls the same function.

The loop does not stream. A round's output is either tool calls or prose and
which one is not known until the response arrives, so an on_delta callback is
invoked once with the finished text, the way the template paths already do it.
Streaming the final round is a later change with a real workload behind it.
"""

from __future__ import annotations

import operator
import time
from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from packages import telemetry
from packages.agent.tools import ToolRegistry, antibody_registry, run_tool
from packages.composer import TurnResult

# Four is the starting cap, raised only on a measured workload that needs more.
MAX_TOOL_CALLS = 4

# Appended once, when the cap is spent, so the reply is composed in the
# knowledge that it is incomplete. Without it the model answers from a partial
# fetch as though the fetch had finished, which reads as a confident claim
# about a catalog it only half read.
BUDGET_NOTE = (
    "The per-turn tool budget for this question is spent. Answer from what you"
    " have already retrieved, and say plainly which lookups you were not able"
    " to run, rather than filling the gap from memory."
)

BUDGET_EXHAUSTED_RESULT = (
    '{"error": "not run: the per-turn tool budget was already spent"}'
)

# LangGraph counts one node execution as one superstep and raises when the
# limit is crossed. The conditional edge already terminates the loop, so this
# only bounds a bug in that edge: worst case is a model call and a tool node
# per budgeted call, plus the final call, plus headroom.
RECURSION_HEADROOM = 4


class LoopState(TypedDict):
    """Everything one turn's loop carries between nodes.

    messages accumulates because both nodes append to the same conversation.
    The counters are absolute rather than accumulated, since each node computes
    them from the state it was handed.
    """

    messages: Annotated[list[dict], operator.add]
    unfulfilled: Annotated[list[str], operator.add]
    tool_calls_made: int
    max_tool_calls: int
    model_calls: int
    text: str
    finish_reason: str | None
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int


@dataclass(frozen=True)
class LoopDeps:
    """Per-turn collaborators, passed through the graph config.

    Held here rather than in the state because none of it is a value the graph
    updates, and rather than in a module global because the client and the tool
    registry are exactly what a test substitutes.
    """

    client: Any
    model: str
    reasoning_effort: str
    max_output_tokens: int | None
    registry: ToolRegistry


@dataclass(frozen=True)
class AgentTurn:
    """One loop's composed reply plus what the loop itself did.

    result is a TurnResult so the loop drops into the composer's return
    contract unchanged. The loop fields sit beside it rather than inside it,
    because the API layer's turn handling is written against the single-shot
    shape and must not have to learn a new one to keep working.
    """

    result: TurnResult
    tool_calls_made: int
    cap_reached: bool
    unfulfilled: list[str] = field(default_factory=list)


def _assistant_message(message: Any) -> dict:
    """The provider's reply as a plain message dict the next call can replay."""
    replayed: dict[str, Any] = {"role": "assistant", "content": message.content}
    calls = getattr(message, "tool_calls", None) or []
    if calls:
        replayed["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in calls
        ]
    return replayed


def _requested_calls(state: LoopState) -> list[dict]:
    """The tool calls the newest assistant message asked for, if any.

    Both the conditional edge and the tools node read the request from here,
    so what the graph routes on and what it executes cannot come apart.
    """
    if not state["messages"]:
        return []
    return state["messages"][-1].get("tool_calls", []) or []


def _model_node(state: LoopState, config: RunnableConfig) -> dict:
    """One model call, offering the tools only while budget remains.

    Withdrawing the tools on the final call is what makes the cap a property of
    the request rather than a rule the model is asked to respect. A model that
    cannot see a tool cannot request one, so the turn ends in prose.
    """
    deps: LoopDeps = config["configurable"]["deps"]
    remaining = state["max_tool_calls"] - state["tool_calls_made"]

    kwargs: dict[str, Any] = {
        "model": deps.model,
        "messages": state["messages"],
        "reasoning_effort": deps.reasoning_effort,
    }
    if deps.max_output_tokens:
        kwargs["max_completion_tokens"] = deps.max_output_tokens
    if remaining > 0:
        kwargs["tools"] = list(deps.registry.definitions)

    with telemetry.llm_span("abbie.agent.model", deps.model) as span:
        response = deps.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        usage = response.usage
        details = getattr(usage, "completion_tokens_details", None) if usage else None
        reasoning = getattr(details, "reasoning_tokens", 0) or 0
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        telemetry.record_usage(
            span,
            deps.model,
            prompt_tokens,
            # Reasoning tokens bill as output, so they belong in the output
            # count or the span understates what the turn cost.
            completion_tokens + reasoning,
            choice.finish_reason,
        )
        span.set_attribute("abbie.tools_offered", remaining > 0)
        span.set_attribute("abbie.tool_calls_remaining", max(remaining, 0))

    return {
        "messages": [_assistant_message(choice.message)],
        "model_calls": state["model_calls"] + 1,
        "text": choice.message.content or "",
        "finish_reason": choice.finish_reason,
        "prompt_tokens": state["prompt_tokens"] + prompt_tokens,
        "completion_tokens": state["completion_tokens"] + completion_tokens,
        "reasoning_tokens": state["reasoning_tokens"] + reasoning,
    }


def _tools_node(state: LoopState, config: RunnableConfig) -> dict:
    """Run the requested calls, up to whatever budget is left.

    A model may request more calls in one message than the cap can pay for, so
    the surplus is answered with a result saying it was not run. Every request
    gets a reply either way: a tool message missing its call is a malformed
    conversation the next request would be rejected for, and the model needs to
    read the gap to be able to state it.
    """
    deps: LoopDeps = config["configurable"]["deps"]
    remaining = state["max_tool_calls"] - state["tool_calls_made"]
    replies: list[dict] = []
    unfulfilled: list[str] = []
    executed = 0

    for call in _requested_calls(state):
        name = call["function"]["name"]
        if executed >= remaining:
            unfulfilled.append(name)
            replies.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": BUDGET_EXHAUSTED_RESULT,
                }
            )
            continue
        executed += 1
        with telemetry.tool_span(f"abbie.tool.{name}", name, call["id"]) as span:
            payload, failed = run_tool(
                deps.registry, name, call["function"]["arguments"]
            )
            span.set_attribute("abbie.tool_failed", failed)
        replies.append(
            {"role": "tool", "tool_call_id": call["id"], "content": payload}
        )

    made = state["tool_calls_made"] + executed
    if made >= state["max_tool_calls"]:
        replies.append({"role": "system", "content": BUDGET_NOTE})

    return {
        "messages": replies,
        "unfulfilled": unfulfilled,
        "tool_calls_made": made,
    }


def _next_step(state: LoopState) -> str:
    """Continue into the tools only while there is budget to run them.

    Checking the budget here as well as withdrawing the tools in the model node
    is deliberate. The withdrawal depends on the provider honoring an absent
    tool list. This check does not, and it is what makes termination a
    property of the graph.
    """
    if _requested_calls(state) and state["tool_calls_made"] < state["max_tool_calls"]:
        return "tools"
    return END


def _build_graph():
    builder = StateGraph(LoopState)
    builder.add_node("model", _model_node)
    builder.add_node("tools", _tools_node)
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", _next_step, {"tools": "tools", END: END})
    builder.add_edge("tools", "model")
    return builder.compile()


# Compiled once. The graph is immutable and carries no per-turn state, which
# all travels in LoopState and the config.
GRAPH = _build_graph()


def run_answer_loop(
    client,
    messages: list[dict],
    model: str,
    reasoning_effort: str,
    max_output_tokens: int | None = None,
    on_delta: Callable[[str], None] | None = None,
    registry: ToolRegistry | None = None,
    max_tool_calls: int = MAX_TOOL_CALLS,
) -> AgentTurn:
    """Run one answer turn as a capped tool loop over the given messages.

    messages is the composer's assembled answer context, so the system prompt,
    the corpus, the history, and any shape hint are exactly what the single-shot
    path would have sent. Only the behavior after the first response differs.
    """
    deps = LoopDeps(
        client=client,
        model=model,
        reasoning_effort=reasoning_effort,
        max_output_tokens=max_output_tokens,
        registry=registry if registry is not None else antibody_registry(),
    )
    initial: LoopState = {
        "messages": list(messages),
        "unfulfilled": [],
        "tool_calls_made": 0,
        "max_tool_calls": max_tool_calls,
        "model_calls": 0,
        "text": "",
        "finish_reason": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "reasoning_tokens": 0,
    }
    start = time.perf_counter()
    final = GRAPH.invoke(
        initial,
        config={
            "configurable": {"deps": deps},
            "recursion_limit": 2 * max_tool_calls + RECURSION_HEADROOM,
        },
    )
    # Whole-loop wall time rather than the sum of the model calls, because a
    # loop's latency is what the visitor waits through, tool time included.
    latency_ms = round((time.perf_counter() - start) * 1000)

    if on_delta and final["text"]:
        on_delta(final["text"])

    return AgentTurn(
        result=TurnResult(
            behavior="answer",
            text=final["text"],
            llm_called=True,
            model=model,
            finish_reason=final["finish_reason"],
            prompt_tokens=final["prompt_tokens"],
            completion_tokens=final["completion_tokens"],
            reasoning_tokens=final["reasoning_tokens"],
            latency_ms=latency_ms,
        ),
        tool_calls_made=final["tool_calls_made"],
        cap_reached=final["tool_calls_made"] >= max_tool_calls,
        unfulfilled=list(final["unfulfilled"]),
    )
