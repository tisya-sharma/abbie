"""Adapter from the transport-free tool library to one provider's call format.

packages.antibody knows nothing about who calls it, which is what lets the
widget call it in process while an MCP server and a Slack app stay thin
adapters over the same functions. This module is one of those adapters: it
publishes the library's argument models as OpenAI function definitions and
dispatches a requested call back to the function. Keeping the provider envelope
here rather than in the library is what stops the library from acquiring a
transport.

Schemas are derived from the Pydantic argument models rather than hand-written,
so there is one definition of each tool's arguments instead of a Python
signature and a JSON Schema that drift apart.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from packages.antibody import (
    GetAntibodyArgs,
    SearchAntibodiesArgs,
    get_antibody,
    search_antibodies,
)

GET_ANTIBODY_DESCRIPTION = (
    "Fetch one catalog entry by its exact identifier. Use when the question"
    " names a specific reagent."
)

SEARCH_ANTIBODIES_DESCRIPTION = (
    "Find catalog entries by target, application, and reactivity species."
    " Every filter is optional. An application missing from an entry's"
    " assessed list is unassessed, which is not the same as a failure."
)


def _tool_parameters(model: type[BaseModel]) -> dict[str, Any]:
    """JSON Schema for one argument model, trimmed to what a model needs.

    Pydantic emits the class docstring as the schema description and a title on
    every node. The docstrings here are written for a maintainer and the titles
    restate the field names, so both are tokens the model pays for and learns
    nothing from. Per-property descriptions are written for the model and stay.
    """
    schema = model.model_json_schema()
    schema.pop("description", None)
    _drop_titles(schema)
    for definition in schema.get("$defs", {}).values():
        definition.pop("description", None)
    return schema


def _drop_titles(node: Any) -> None:
    if isinstance(node, dict):
        node.pop("title", None)
        for value in node.values():
            _drop_titles(value)
    elif isinstance(node, list):
        for value in node:
            _drop_titles(value)


@dataclass(frozen=True)
class ToolRegistry:
    """The tools one loop may call, definitions and implementations together.

    Passed in rather than read from a module global, because the library is
    constructed several ways (public widget, staff surface, extract job) and is
    substituted in tests. A registry whose definitions and functions came from
    different places is a tool the model can request and nothing can run, so
    they travel as one object.
    """

    definitions: tuple[dict[str, Any], ...]
    functions: dict[str, Callable[..., BaseModel]]
    arguments: dict[str, type[BaseModel]]


def _definition(name: str, description: str, args: type[BaseModel]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": _tool_parameters(args),
        },
    }


def antibody_registry() -> ToolRegistry:
    """The Stage 2 catalog tools, currently backed by placeholder records.

    A function rather than a constant so a caller holds its own registry and no
    import-time work happens, which is the same reason the library refuses a
    module-global connection.
    """
    return ToolRegistry(
        definitions=(
            _definition("get_antibody", GET_ANTIBODY_DESCRIPTION, GetAntibodyArgs),
            _definition(
                "search_antibodies", SEARCH_ANTIBODIES_DESCRIPTION, SearchAntibodiesArgs
            ),
        ),
        functions={
            "get_antibody": get_antibody,
            "search_antibodies": search_antibodies,
        },
        arguments={
            "get_antibody": GetAntibodyArgs,
            "search_antibodies": SearchAntibodiesArgs,
        },
    )


def _error(reason: str) -> str:
    """The payload a failed call returns to the model.

    A failure is reported into the conversation rather than raised, so the turn
    continues with one tool missing instead of ending. The model can then say
    what it could not check, which is the outcome a visitor is better served by
    than an apology for the whole reply.
    """
    return json.dumps({"error": reason})


def run_tool(registry: ToolRegistry, name: str, arguments: str) -> tuple[str, bool]:
    """Execute one requested call, returning its JSON payload and whether it failed.

    Every failure mode a model can create is handled the same way: an unknown
    tool name, arguments that are not JSON, arguments that do not validate, and
    an implementation that raises. The last one catches Exception on purpose.
    A tool is the boundary with code this loop does not own, and the alternative
    to a broad catch here is a visitor losing an entire answer because one
    lookup hit a driver bug.
    """
    function = registry.functions.get(name)
    model = registry.arguments.get(name)
    if function is None or model is None:
        return _error(f"no such tool: {name}"), True

    try:
        raw = json.loads(arguments) if arguments.strip() else {}
    except json.JSONDecodeError:
        return _error("arguments were not valid JSON"), True
    if not isinstance(raw, dict):
        return _error("arguments must be a JSON object"), True

    try:
        parsed = model.model_validate(raw)
    except ValidationError as exc:
        return _error(f"invalid arguments: {exc.error_count()} field problems"), True

    try:
        result = function(**parsed.model_dump())
    except Exception as exc:
        return _error(f"{name} failed: {type(exc).__name__}"), True
    return result.model_dump_json(), False
