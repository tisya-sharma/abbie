"""Serve the routed Abbie pipeline over HTTP with streamed SSE turns.

This is the CLI's turn re-expressed as a localhost web endpoint: the same
classify -> respond -> cite -> follow-up sequence as apps/cli/chat.py, with
the same per-session history and covered-set state, streamed to one static
page. The composer's on_delta callback is synchronous, so each turn runs on
a worker thread that feeds a queue the SSE generator drains — that queue is
the whole bridge. Demo transport only: no persistence, no accounts, and
nothing here is deployment configuration.
"""

from __future__ import annotations

import json
import os
import queue
import sys
import threading
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

from packages.composer import ComposerPrompts, read_prompt_file, respond
from packages.corpus_loader import (
    build_system_message,
    cite_resolver,
    extract_citations,
)
from packages.export import checklist_concepts, render_checklist
from packages.envfile import load_env_file
from packages.guardrail import (
    StreamScrubber,
    is_publishable,
    leak_scan,
    scrub_and_number,
    scrub_text,
)
from packages.router import classify
from packages import telemetry

load_env_file()

PROMPTS_DIR = REPO_ROOT / "apps" / "api" / "prompts"
STATIC_DIR = REPO_ROOT / "apps" / "api" / "static"
MODEL = os.environ.get("ABBIE_MODEL", "gpt-5-mini")
ROUTER_MODEL = os.environ.get("ABBIE_ROUTER_MODEL", "gpt-5-mini")
REASONING_EFFORT = "low"
MAX_FOLLOW_UPS = 4


def read_prompt(name: str) -> str:
    """Read one prompt file, failing fast with a clear message if missing."""
    path = PROMPTS_DIR / name
    try:
        return read_prompt_file(path)
    except FileNotFoundError:
        raise SystemExit(f"missing prompt file: {path}")


def make_client():
    """Build the shared OpenAI client from the environment.

    The import lives inside the function so the module can be read without
    the SDK installed, matching the CLI. One client is shared across worker
    threads because the underlying httpx client is thread-safe and pools
    connections; every per-turn datum travels as call arguments.
    """
    from openai import OpenAI

    return OpenAI()


if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit(
        "OPENAI_API_KEY is not set. Paste IPI's key into keys.env at the repo root,"
        " or export it in this shell."
    )

client = make_client()
try:
    ANSWER_SYSTEM, CONCEPTS = build_system_message(read_prompt("system.md"))
except ValueError as exc:
    raise SystemExit(f"{exc}\nrefusing to start")

ROUTER_PROMPT = read_prompt("router.md")
PROMPTS = ComposerPrompts(
    answer_system=ANSWER_SYSTEM,
    redirect_system=read_prompt("redirect.md"),
    refuse_text=read_prompt("refuse.md"),
    abstain_template=read_prompt("abstain.md"),
)


@dataclass
class Session:
    """One browser session's conversation state, the CLI's locals per id.

    history and covered mirror apps/cli/chat.py exactly: history is appended
    for all four behaviors and never trimmed, covered records cited concept
    ids to keep follow-up offers fresh. The lock serializes turns within a
    session, which is the concurrency the CLI actually has — its input loop
    blocks until a turn finishes. Nothing is persisted.
    """

    # Only ever used to group a conversation's spans on the trace. It is a
    # browser-supplied opaque string, never an identity: there are no accounts
    # here and nothing links a session to a person.
    session_id: str = ""
    history: list[dict] = field(default_factory=list)
    covered: set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)
    # Cited ids per answered turn, kept here rather than sent to the page. The
    # export needs to know which concepts a reply drew on, and concept ids are
    # internal identifiers the leak scan treats as a release-blocking failure
    # if they reach a user surface, so the page refers to a turn by index and
    # the ids never leave the server.
    turn_concepts: list[list[str]] = field(default_factory=list)


SESSIONS: dict[str, Session] = {}


class ChatRequest(BaseModel):
    """One turn's input from the page."""

    message: str
    session_id: str


class ChecklistRequest(BaseModel):
    """Which answered turn to build the downloadable checklist from.

    A turn index rather than a list of concepts, because concept ids are
    internal identifiers and the page must never hold them. The server looks
    up what that turn actually cited.
    """

    session_id: str
    turn_index: int


def follow_ups_for(cited: list[str], concepts: dict, covered: set[str]) -> list[str]:
    """Graph-derived next topics: leads_to of cited concepts, minus covered.

    Duplicated from apps/cli/chat.py rather than imported, because the CLI
    is a script with import-time side effects, not a library.
    """
    offers: list[str] = []
    for cid in cited:
        for target in concepts[cid].leads_to:
            if target in concepts and target not in covered and target not in offers:
                offers.append(target)
    return offers


OUTLINE_OFFER_LABEL = "Outline the whole process"

FALLBACK_MESSAGE = (
    "I had trouble putting that reply together. Could you try asking another way?"
)


def pending_offer(history: list[dict]) -> str | None:
    """The closing line of the last assistant reply, scrubbed for the router.

    This is the offer a bare "yes please" would be accepting. Scrubbing keeps
    citation markers out of the router's context.
    """
    for message in reversed(history):
        if message.get("role") == "assistant":
            lines = [
                line.strip()
                for line in scrub_text(message.get("content", "")).splitlines()
                if line.strip()
            ]
            return lines[-1] if lines else None
    return None


SOURCE_DISPLAY_FIELDS = ("short", "journal", "title")


# The scrubber's resolver, shared with the eval scorer so one policy decides
# what a citation may show. An unknown id resolves to nothing rather than
# raising: the model can emit a marker for anything, and a bad id should cost
# the reply its citation, not the whole turn.
publishable_urls = cite_resolver(CONCEPTS)


def source_index(concepts: dict) -> dict[str, dict]:
    """Display fields for every citable source in the corpus, keyed by url.

    One entry per paper rather than per citing concept. A url is the paper, so
    two concepts citing it describe the same thing, and resolving the display
    fields once is what guarantees a pill streamed mid-reply carries the same
    wording as the row the done frame renders beneath it.

    The display fields are optional by design: a source that lacks one still
    renders, just with that line short.
    """
    index: dict[str, dict] = {}
    for concept in concepts.values():
        for source in concept.sources:
            url = source.get("url")
            if not is_publishable(source) or url in index:
                continue
            link = {"label": source.get("label", url), "url": url}
            for field in SOURCE_DISPLAY_FIELDS:
                if source.get(field):
                    link[field] = source[field]
            index[url] = link
    return index


SOURCES_BY_URL = source_index(CONCEPTS)


def sources_for(urls: list[str]) -> list[dict]:
    """Further-reading links in the order the reply's citations numbered them.

    The order is the scrubber's, because a row's position here is the number
    its pill points at. IPI-authored concepts ground answers without producing
    a visible source, which is expected and simply cites nothing. Nothing is
    truncated: a cap would strand a citation pointing at a row that never
    renders.
    """
    return [SOURCES_BY_URL[url] for url in urls if url in SOURCES_BY_URL]


def origin_is_local(origin: str) -> bool:
    """Return whether a browser Origin header names localhost itself.

    This is a refusal, not CORS: nothing is relaxed. Browsers attach Origin
    to cross-site POSTs, and a page on any other site can fire a
    no-preflight POST at a localhost port and spend the OpenAI key blind.
    Requests without an Origin header (curl, same-origin GET) never reach
    this check.
    """
    return urlparse(origin).hostname in ("localhost", "127.0.0.1", "::1")


def sse(event: str, payload: dict) -> str:
    """Format one SSE frame.

    json.dumps escapes newlines, so every frame is exactly three lines and a
    delta carrying paragraph breaks cannot desync the event framing.
    """
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def run_turn(
    session: Session, question: str, out: queue.Queue[tuple[str, dict] | None]
) -> None:
    """Run one routed turn on a worker thread, emitting frames to the queue.

    The composer blocks on the OpenAI SDK, so the whole turn lives on this
    thread and the endpoint's generator just drains the queue. The route
    frame goes out before generation so the page can badge the reply early.
    State is mutated before the done frame is built because its follow-ups
    depend on the updated covered set, and the only call that can raise
    precedes the first history append, so a failed turn leaves the session
    as if the question was never asked. The sentinel is emitted in finally
    so a failure can never leave the stream waiting.
    """
    try:
        with session.lock, telemetry.turn_span(
            session.session_id, len(session.turn_concepts)
        ) as turn:
            with telemetry.llm_span("abbie.router", ROUTER_MODEL) as span:
                route = classify(
                    client,
                    question,
                    ROUTER_MODEL,
                    ROUTER_PROMPT,
                    context=pending_offer(session.history),
                )
                telemetry.record_usage(
                    span, route.model, route.prompt_tokens, route.completion_tokens
                )
                span.set_attribute("abbie.behavior", route.behavior)
                span.set_attribute("abbie.fallback", route.fallback)
                if route.form:
                    span.set_attribute("abbie.form", route.form)
                telemetry.record_content(span, question, None)
            out.put(
                (
                    "route",
                    {
                        "behavior": route.behavior,
                        "subject": route.subject,
                        "fallback": route.fallback,
                        "form": route.form,
                    },
                )
            )
            # One scrubber per turn: citation markers become source numbers in
            # the deltas the browser sees, while result.text stays raw for
            # citation extraction and history. flush() must run after the
            # stream ends or a reply ending in a marker loses its tail.
            scrubber = StreamScrubber(publishable_urls)
            # The page cannot draw a citation pill from an ordinal alone, and
            # the sources list only arrives with the done frame, after the text
            # that cites it. So each source goes out as its number is assigned,
            # which puts it on the wire ahead of the delta that references it
            # and lets a pill render complete the moment it appears.
            sent_sources = 0

            def drain_sources() -> None:
                nonlocal sent_sources
                keys = scrubber.keys
                while sent_sources < len(keys):
                    link = SOURCES_BY_URL[keys[sent_sources]]
                    sent_sources += 1
                    out.put(("source", dict(link, n=sent_sources)))

            def emit_delta(delta: str) -> None:
                visible = scrubber.feed(delta)
                drain_sources()
                if visible:
                    out.put(("delta", {"text": visible}))

            with telemetry.llm_span("abbie.composer", MODEL) as span:
                result = respond(
                    client,
                    route,
                    question,
                    PROMPTS,
                    MODEL,
                    REASONING_EFFORT,
                    history=session.history,
                    on_delta=emit_delta,
                )
                # Refuse and abstain are templates with no model call, so they
                # carry no model or usage to report.
                if result.llm_called and result.model:
                    telemetry.record_usage(
                        span,
                        result.model,
                        result.prompt_tokens,
                        # Reasoning tokens bill as output, so they belong in the
                        # output count or the span understates what the turn cost.
                        result.completion_tokens + result.reasoning_tokens,
                        result.finish_reason,
                    )
                    telemetry.record_content(span, None, result.text)
                span.set_attribute("abbie.llm_called", result.llm_called)
                span.set_attribute("abbie.behavior", result.behavior)
            tail = scrubber.flush()
            drain_sources()
            if tail:
                out.put(("delta", {"text": tail}))

            cited = extract_citations(result.text, CONCEPTS)
            covered_after = session.covered | set(cited)
            offers = follow_ups_for(cited, CONCEPTS, covered_after)
            follow_ups = [
                {"label": CONCEPTS[fid].ask or CONCEPTS[fid].title}
                for fid in offers
            ]
            # A procedural first touch withholds the full process behind an
            # offer; the chip makes that door clickable. Clicking sends the
            # label as an ordinary message, which the router classifies as
            # acceptance against the pending offer.
            if route.behavior == "answer" and route.form == "procedural":
                follow_ups.insert(0, {"label": OUTLINE_OFFER_LABEL})
            follow_ups = follow_ups[:MAX_FOLLOW_UPS]
            # Recomputed from the finished reply rather than read off the
            # streaming scrubber, so the numbering and the guarded text hold
            # even on a path that never streamed a delta.
            visible, source_keys = scrub_and_number(result.text, publishable_urls)
            sources = sources_for(source_keys)

            # Fail-closed backstop: nothing that names the corpus may reach
            # the page. On a hit the frame tells the page to replace the
            # already-streamed body, and the session is left as if the turn
            # never happened. What gets scanned is the numbered text the
            # visitor actually read, not a differently scrubbed variant of it.
            surfaces = [visible]
            surfaces.extend(f["label"] for f in follow_ups)
            # Every string a source puts on the page, not just its label —
            # the scan is the backstop, so a field it does not read is a field
            # that reaches the visitor unchecked.
            surfaces.extend(
                value
                for source in sources
                for key, value in source.items()
                if key != "url"
            )
            with telemetry.step_span("abbie.guardrail") as span:
                findings = [
                    finding
                    for text in surfaces
                    for finding in leak_scan(text, set(CONCEPTS))
                ]
                span.set_attribute("abbie.leak_findings", len(findings))
                if findings:
                    span.set_attribute("abbie.leak_reasons", findings)
            if findings:
                print(f"leak scan blocked a reply: {findings}", file=sys.stderr)
                # Withdrawn from the visitor, kept on the trace. A blocked turn
                # is both the highest-signal security event this system produces
                # and its most valuable eval case, so the session forgets it and
                # the trace does not.
                turn.set_attribute("abbie.outcome", "blocked")
                turn.set_attribute("abbie.leak_reasons", findings)
                telemetry.record_content(turn, question, result.text)
                out.put(("error", {"message": FALLBACK_MESSAGE, "replace": True}))
                return

            session.history.append({"role": "user", "content": question})
            session.history.append({"role": "assistant", "content": result.text})
            session.covered.update(cited)
            session.turn_concepts.append(cited)
            turn.set_attribute("abbie.outcome", "answered")
            turn.set_attribute("abbie.behavior", result.behavior)
            turn.set_attribute("abbie.cited_count", len(cited))
            turn.set_attribute(
                "abbie.latency_ms", route.latency_ms + result.latency_ms
            )
            out.put(
                (
                    "done",
                    {
                        "behavior": result.behavior,
                        "subject": route.subject,
                        "fallback": route.fallback,
                        "sources": sources,
                        "follow_ups": follow_ups,
                        "latency_ms": route.latency_ms + result.latency_ms,
                        "turn_index": len(session.turn_concepts) - 1,
                        "checklist": bool(checklist_concepts(CONCEPTS, cited)),
                    },
                )
            )
    except Exception as exc:
        print(f"turn failed: {exc!r}", file=sys.stderr)
        out.put(("error", {"message": FALLBACK_MESSAGE}))
    finally:
        out.put(None)


def stream_frames(out: queue.Queue[tuple[str, dict] | None]) -> Iterator[str]:
    """Yield SSE frames from the queue until the worker's sentinel arrives."""
    while True:
        item = out.get()
        if item is None:
            return
        event, payload = item
        yield sse(event, payload)


app = FastAPI(title="abbie")


@app.on_event("startup")
def start_telemetry() -> None:
    """Install tracing, reporting to stderr whether an exporter was found.

    Absence is normal rather than an error: with no backend configured the
    pipeline runs identically and spans are discarded, so a laptop needs no
    account and no keys.
    """
    if telemetry.configure():
        print("tracing: exporting spans", file=sys.stderr)
    else:
        print("tracing: no exporter configured, spans discarded", file=sys.stderr)


@app.on_event("shutdown")
def stop_telemetry() -> None:
    """Flush buffered spans, which are otherwise lost on exit."""
    telemetry.shutdown()


@app.get("/")
def index() -> FileResponse:
    """Serve the demo page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat")
def chat(req: ChatRequest, request: Request) -> StreamingResponse:
    """Stream one routed turn as SSE: route, deltas, then done or error.

    The endpoint is sync on purpose: Starlette iterates the generator in a
    threadpool, so its blocking queue reads never touch the event loop.
    Cross-origin POSTs are refused before any work — see origin_is_local.
    """
    origin = request.headers.get("origin")
    if origin is not None and not origin_is_local(origin):
        raise HTTPException(status_code=403, detail="cross-origin requests are refused")
    question = req.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="message must not be empty")
    session = SESSIONS.setdefault(
        req.session_id, Session(session_id=req.session_id)
    )
    out: queue.Queue[tuple[str, dict] | None] = queue.Queue()
    threading.Thread(
        target=run_turn, args=(session, question, out), daemon=True
    ).start()
    return StreamingResponse(stream_frames(out), media_type="text/event-stream")


@app.post("/export/checklist")
def export_checklist(req: ChecklistRequest, request: Request) -> Response:
    """Return the bench checklist for one answered turn as a PDF.

    Nothing the model wrote reaches this document. The turn's cited concepts
    select which reviewed frontmatter blocks are laid into a fixed template,
    so the same turn always produces the same bytes and the wording is
    something a scientist signed off on rather than something regenerated per
    request.
    """
    origin = request.headers.get("origin")
    if origin is not None and not origin_is_local(origin):
        raise HTTPException(status_code=403, detail="cross-origin requests are refused")
    session = SESSIONS.get(req.session_id)
    if session is None or not 0 <= req.turn_index < len(session.turn_concepts):
        raise HTTPException(status_code=404, detail="no such turn in this session")

    document = render_checklist(
        CONCEPTS,
        session.turn_concepts[req.turn_index],
        generated_on=date.today().strftime("%d %B %Y"),
    )
    if document is None:
        raise HTTPException(
            status_code=404, detail="that answer has no checklist behind it"
        )
    return Response(
        content=document.body,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{document.filename}"'
        },
    )
