"""neatlogs tracing integration.

Follows https://neatlogs.com/hackathon/neatlogs-setup-guide.html:
  pip install neatlogs openai
  neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name=...)
  client = neatlogs.wrap(OpenAI())   # auto-traces every model call
  neatlogs.flush() / neatlogs.shutdown()

Tool executions are recorded as structured events to a local JSONL evidence
file (runs/<domain>/<ts>/trace.jsonl) AND, when the SDK exposes a span API,
mirrored into neatlogs. Everything degrades to a no-op when the SDK or the
Project API key (the top key in Settings, NOT the nlw_ HTTP key) is missing.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import neatlogs
    _SDK = True
except ImportError:  # pragma: no cover
    neatlogs = None  # type: ignore
    _SDK = False

_trace_file: Path | None = None
_run_id: str = ""


def _key() -> str:
    return os.environ.get("NEATLOGS_API_KEY", "").strip()


def init_tracing(workflow_name: str = "vendorlens-investigation") -> bool:
    """Init neatlogs once. Returns True when live tracing is active."""
    if _SDK and _key():
        neatlogs.init(api_key=_key(),
                      endpoint="https://ingest.neatlogs.com",
                      workflow_name=workflow_name)
        return True
    return False


def wrap_client(client):
    """Wrap an OpenAI-compatible client so model calls are auto-traced."""
    if _SDK and _key():
        return neatlogs.wrap(client)
    return client


@contextmanager
def workflow(name: str, **attrs):
    """Root WORKFLOW span for one investigation run.

    Groups the whole agent loop (planner, tool steps, observer) under one
    trace in the neatlogs dashboard. No-op when the SDK or key is missing.
    """
    if _SDK and _key():
        with neatlogs.trace(name, kind="WORKFLOW", **attrs):
            yield
    else:
        yield


def set_trace_file(path: Path, run_id: str) -> None:
    global _trace_file, _run_id
    _trace_file = path
    _run_id = run_id


def log_event(kind: str, name: str, payload: dict | None = None) -> None:
    """Append a structured event to the local JSONL evidence log."""
    if _trace_file is None:
        return
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": _run_id,
        "kind": kind,
        "name": name,
        "payload": payload or {},
    }
    with _trace_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")


@contextmanager
def trace_tool(name: str, args: dict | None = None):
    """Time a tool execution; record status/latency to the local evidence log
    and, when the neatlogs SDK + key are present, emit a nested child TOOL
    span under the run's WORKFLOW span (mirrors trace.jsonl)."""
    start = time.perf_counter()
    log_event("tool_start", name, {"args": args or {}})
    span = None
    if _SDK and _key():
        try:
            span = neatlogs.trace(name, kind="TOOL", **(args or {}))
            span.__enter__()
        except Exception:
            span = None
    try:
        yield
    except Exception as exc:  # noqa: BLE001
        log_event("tool_error", name, {
            "error": f"{type(exc).__name__}: {exc}",
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
        })
        if span is not None:
            try:
                span.__exit__(type(exc), exc, exc.__traceback__)
            except Exception:
                pass
        raise
    else:
        log_event("tool_end", name, {
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
        })
        if span is not None:
            try:
                span.__exit__(None, None, None)
            except Exception:
                pass


def flush() -> None:
    if _SDK and _key():
        try:
            neatlogs.flush()
        except Exception:  # tracing must never break the run
            pass


def shutdown() -> None:
    if _SDK and _key():
        try:
            neatlogs.shutdown()
        except Exception:
            pass
