"""VendorLens agent loop: planner -> tool executor -> observer -> replan.

- Persistent state dict across steps (findings, retries, plan history).
- Per-step retry with exponential backoff; failures recorded, never fatal.
- Every step emits neatlogs spans (LLM calls auto-traced via the wrapped
  client; tool executions logged as structured events to trace.jsonl).
- Observer replans after surprising results (LLM mode) or follows the
  scripted plan (demo mode).
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from . import brief, llm, risk, tracing
from .tools import TOOLS

DEMO_PLAN = [
    {"id": "s1", "tool": "whois_lookup",
     "args": {}, "why": "Domain age is the cheapest strong signal."},
    {"id": "s2", "tool": "dns_lookup",
     "args": {}, "why": "Missing MX records suggest a non-business."},
    {"id": "s3", "tool": "tls_inspect",
     "args": {}, "why": "Certificate hygiene check."},
    {"id": "s4", "tool": "fetch_homepage",
     "args": {}, "why": "Scam-phrase analysis of vendor copy."},
    {"id": "s5", "tool": "web_search_reports",
     "args": {}, "why": "Independent reports and reviews."},
    {"id": "s6", "tool": "crustdata_enrich",
     "args": {}, "why": "Firmographic confirmation of a real company."},
]

MAX_RETRIES = 3


def _sanitize_steps(raw) -> list[dict]:
    """Coerce LLM-produced plan/observer steps into the executor schema
    (id, tool, args, why). Drops malformed steps or unknown tool names so a
    field the model omitted can never crash the run."""
    out: list[dict] = []
    for i, step in enumerate(raw or [], 1):
        if not isinstance(step, dict):
            continue
        tool = step.get("tool")
        if tool not in TOOLS:
            continue
        args = step.get("args")
        if not isinstance(args, dict):
            args = {}
        out.append({"id": str(step.get("id") or f"step{i}"),
                    "tool": tool, "args": args, "why": step.get("why", "")})
    return out


async def execute_with_retry(step: dict, ctx: dict, state: dict) -> dict:
    tool = TOOLS[step["tool"]]
    args = dict(step["args"])
    args.setdefault("domain", state["domain"])
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        with tracing.trace_tool(step["tool"], args):
            result = await tool.run(args, ctx)
        if result.get("ok"):
            if attempt > 1:
                state["retries"][step["id"]] = attempt
            return result
        last_error = result.get("error")
        tracing.log_event("tool_retry", step["tool"],
                          {"attempt": attempt, "error": last_error})
        await asyncio.sleep(2 ** attempt)  # exponential backoff
    state["retries"][step["id"]] = MAX_RETRIES
    return {"ok": False, "error": f"gave up after {MAX_RETRIES}: {last_error}",
            "sources": []}


async def run_investigation(domain: str, demo: bool = False,
                          run_id: str | None = None,
                          no_llm: bool = False) -> dict:
    run_id = run_id or uuid.uuid4().hex[:8]
    state = {
        "domain": domain,
        "run_id": run_id,
        "started": datetime.now(timezone.utc).isoformat(),
        "findings": {},
        "retries": {},
        "plan_history": [],
    }
    ctx = {"demo": demo}
    tracing.log_event("run_start", "investigation",
                      {"domain": domain, "demo": demo})

    if demo or no_llm:
        # Deterministic plan, no LLM needed. In --demo the tools also return
        # canned data; in --no-llm they run live.
        plan = [dict(s, args={**s["args"], "domain": domain})
                for s in DEMO_PLAN]
        client = model = None
    else:
        client, model = llm.get_client()
        plan = _sanitize_steps(llm.plan_with_llm(client, model, domain))
        if not plan:
            # Model returned nothing usable; fall back to the fixed plan so the
            # investigation still runs and produces a brief.
            plan = [dict(s, args={**s["args"], "domain": domain})
                    for s in DEMO_PLAN]

    queue = list(plan)
    while queue:
        step = queue.pop(0)
        state["plan_history"].append(step)
        tracing.log_event("step_start", step["id"],
                          {"tool": step["tool"], "why": step.get("why")})
        result = await execute_with_retry(step, ctx, state)
        state["findings"][step["tool"]] = result
        tracing.log_event("step_end", step["id"],
                          {"ok": result.get("ok")})
        # Observer: replan on surprising results (LLM live mode only).
        if not demo and not no_llm and client is not None:
            try:
                extra = _sanitize_steps(
                    llm.replan_with_llm(client, model, domain, state,
                                        {"step": step["id"],
                                         "result_ok": result.get("ok")}))
                for s in extra:
                    s.setdefault("args", {})["domain"] = domain
                queue.extend(extra)
            except Exception:
                pass  # observer is advisory; the run continues

    assessment = risk.assess(domain, state["findings"])
    state["assessment"] = assessment
    tracing.log_event("run_end", "investigation",
                      {"score": assessment["score"],
                       "band": assessment["band"]})
    state["brief_md"] = brief.render(assessment, state["findings"],
                                     {"run_id": run_id})
    return state
