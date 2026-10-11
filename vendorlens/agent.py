"""VendorLens agent loop: planner -> tool executor -> observer -> replan.

- Persistent state dict across steps (findings, step history, retries).
- One structured retry layer at the agent: only transient failures are
  retried, with backoff + jitter; recovery is emitted explicitly (P1.3).
- The observer sees a structured summary of each result (not just ok/error),
  plus the risk signals found so far, and can add follow-up steps (LLM mode).
- A deterministic, non-LLM "rule-based replanning" path always runs, so there
  is visible adaptive behaviour even in --demo / --no-llm:
    * a domain under a year old triggers a phishing-feed deep check;
    * a homepage fetch that fails on https://<apex>/ is retried on www.
- Every step, retry and observer decision is logged to trace.jsonl.
"""
from __future__ import annotations

import asyncio
import json
import random
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from . import brief, llm, risk, tracing, verify
from .tools import TOOLS
from .tools import _http

# The default plan runs the core keyless tools. The phishing-feed check is
# deliberately NOT in the base plan: the rule-based observer adds it when a
# domain looks young, so adaptive behaviour is visible in the trace.
DEMO_PLAN = [
    {"id": "s1", "tool": "rdap_lookup",
     "args": {}, "why": "Registration age is the cheapest strong signal."},
    {"id": "s2", "tool": "doh_dns",
     "args": {}, "why": "Does the domain resolve, and does it take mail?"},
    {"id": "s3", "tool": "tls_inspect",
     "args": {}, "why": "Certificate hygiene check."},
    {"id": "s4", "tool": "ct_logs",
     "args": {}, "why": "Certificate history and subdomains show an "
                        "established org."},
    {"id": "s5", "tool": "urlscan_reputation",
     "args": {}, "why": "Independent web-scan verdicts for the domain."},
    {"id": "s6", "tool": "fetch_homepage",
     "args": {}, "why": "Homepage scam-copy + security-posture analysis."},
    {"id": "s7", "tool": "web_search_reports",
     "args": {}, "why": "Independent reports and reviews."},
    {"id": "s8", "tool": "crustdata_enrich",
     "args": {}, "why": "Firmographic confirmation of a real company."},
]

MAX_STEPS = 14          # hard cap on tool steps in one run
MAX_LLM_REPLANS = 3     # cap on LLM observer replan calls
MAX_ATTEMPTS = 3        # 1 try + 2 retries, transient only


def _sanitize_steps(raw, domain: str) -> list[dict]:
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
        raw_args = step.get("args")
        args = dict(raw_args) if isinstance(raw_args, dict) else {}
        args.setdefault("domain", domain)
        out.append({"id": str(step.get("id") or f"step{i}"),
                    "tool": tool, "args": args, "why": step.get("why", "")})
    return out


def _akey(step: dict) -> str:
    return json.dumps(step.get("args", {}), sort_keys=True, default=str)


def _slim_result(tool: str, result: dict) -> dict:
    d = result.get("data") or {}
    keys = ("found", "age_days", "cert_count", "earliest_cert",
            "subdomain_count", "total_scans", "malicious_scans", "listed",
            "self_signed", "days_left", "status_code")
    out = {"tool": tool, "ok": bool(result.get("ok"))}
    if out["ok"]:
        out.update({k: d[k] for k in keys if k in d})
    else:
        out["error"] = (result.get("error") or "")[:160]
    return out


async def _backoff(attempt: int, retry_after):
    base = 0.6 * (2 ** (attempt - 1))
    wait = base + (0.2 + random.random() * 0.3)
    if isinstance(retry_after, (int, float)) and retry_after > 0:
        wait = min(retry_after, 30.0)
    await asyncio.sleep(min(wait, 3.0))


async def execute_with_retry(step: dict, ctx: dict, state: dict) -> dict:
    tool_name = step["tool"]
    tool = TOOLS[tool_name]
    args = dict(step["args"])
    args.setdefault("domain", state["domain"])
    inject = ctx.get("inject", {}) or {}
    last_error = None
    attempts_used = 0
    start = time.perf_counter()

    def record(result):
        state["step_results"].append({
            "id": step["id"], "tool": tool_name,
            "ok": bool(result.get("ok")), "attempts": attempts_used,
            "error": result.get("error"),
            "injected": bool(result.get("_injected")),
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
        })
        if attempts_used > 1:
            state["retries"][step["id"]] = attempts_used

    for attempt in range(1, MAX_ATTEMPTS + 1):
        # Fault injection (labelled on camera): fail the first n attempts.
        if inject.get(tool_name, 0) > 0:
            inject[tool_name] -= 1
            attempts_used = attempt
            last_error = "simulated 503 Service Unavailable (fault injection)"
            tracing.log_event("tool_retry", tool_name, {
                "attempt": attempt, "injected": True, "error": last_error})
            result = {"ok": False, "error": last_error, "sources": [],
                      "_injected": True}
            if attempt < MAX_ATTEMPTS and _http.is_transient_error(last_error):
                await _backoff(attempt, None)
                continue
            record(result)
            return result
        with tracing.trace_tool(tool_name, args):
            result = await tool.run(args, ctx)
        attempts_used = attempt
        if result.get("ok"):
            if attempt > 1:
                tracing.log_event("tool_recovered", tool_name,
                                  {"attempts": attempt})
            record(result)
            return result
        last_error = result.get("error")
        if not _http.is_transient_error(last_error):
            # Deterministic failure: record once, do not sleep (P1.3).
            tracing.log_event("tool_failed", tool_name,
                              {"attempt": attempt, "error": last_error,
                               "transient": False})
            record(result)
            return result
        tracing.log_event("tool_retry", tool_name,
                          {"attempt": attempt, "error": last_error})
        if attempt < MAX_ATTEMPTS:
            await _backoff(attempt, result.get("retry_after"))

    final = {"ok": False,
             "error": f"gave up after {attempts_used}: {last_error}",
             "sources": []}
    tracing.log_event("tool_failed", tool_name,
                      {"attempts": attempts_used, "error": last_error,
                       "gave_up": True})
    record(final)
    return final


def _rule_replan(step: dict, result: dict, state: dict, domain: str,
                 seen: set) -> list[dict]:
    """Deterministic adaptive planning. Returns extra steps (already domain-
    stamped) when a result warrants one. Always runs, even with no LLM."""
    extras: list[dict] = []
    tool = step["tool"]
    data = result.get("data") or {}

    # 1) A young domain deserves an abuse-feed check it may not have had.
    if tool == "rdap_lookup" and result.get("ok") and data.get("found"):
        age = data.get("age_days")
        if age is not None and age < 365 and ("phishtank_check", _pkey(domain)) \
                not in seen and "phishtank_check" not in state["findings"]:
            extras.append({"id": "rule-phish", "tool": "phishtank_check",
                           "args": {"domain": domain},
                           "why": "young domain: verify against the "
                                  "phishing feed"})

    # 2) A homepage fetch that failed on the apex may work on www.
    if tool == "fetch_homepage" and not result.get("ok") \
            and not domain.startswith("www.") \
            and ("fetch_homepage", _pkey("www." + domain)) not in seen:
        extras.append({"id": "rule-www", "tool": "fetch_homepage",
                       "args": {"domain": "www." + domain},
                       "why": "apex fetch failed; retry the www host"})

    return extras


def _pkey(domain: str) -> str:
    return json.dumps({"domain": domain}, sort_keys=True)


async def run_investigation(domain: str, demo: bool = False,
                            run_id: str | None = None, no_llm: bool = False,
                            scenario: str | None = None,
                            inject: dict | None = None,
                            tag: str | None = None) -> dict:
    run_id = run_id or uuid.uuid4().hex[:8]
    mode = "demo" if demo else ("no-llm" if no_llm else "live")
    ctx = {"demo": demo, "scenario": scenario, "inject": dict(inject or {})}
    state = {
        "domain": domain, "run_id": run_id, "mode": mode,
        "tag": tag,
        "started": datetime.now(timezone.utc).isoformat(),
        "findings": {}, "step_results": [], "retries": {},
        "plan_history": [], "replans": {"llm": 0, "rule": 0},
    }
    tracing.log_event("run_start", "investigation",
                      {"domain": domain, "mode": mode, "scenario": scenario,
                       "tag": tag, "inject": inject or {}})

    if demo or no_llm:
        plan = _sanitize_steps(DEMO_PLAN, domain)
        client = model = None
    else:
        client, model = llm.get_client()
        plan = _sanitize_steps(llm.plan_with_llm(client, model, domain), domain)
        if not plan:
            plan = _sanitize_steps(DEMO_PLAN, domain)
            tracing.log_event("planner_fallback", "investigation",
                              {"reason": "model returned no usable plan"})

    queue: deque = deque(plan)
    seen = {(s["tool"], _akey(s)) for s in plan}
    state["plan_history"] = list(plan)
    steps_done = 0
    llm_replans = 0

    def enqueue(extras, reason, kind, cur_step_id):
        added = []
        for s in extras:
            if steps_done + len(queue) + len(added) >= MAX_STEPS:
                tracing.log_event("replan", cur_step_id, {
                    "kind": kind, "reason": "skipped: at step budget",
                    "added": added, "queue_depth": len(queue)})
                break
            key = (s["tool"], _akey(s))
            if key in seen:
                continue
            seen.add(key)
            queue.append(s)
            state["plan_history"].append(s)
            added.append(s["id"])
        tracing.log_event("replan", cur_step_id, {
            "kind": kind,
            "reason": reason if added else f"{reason}: no change",
            "added": added, "queue_depth": len(queue)})
        if added:
            state["replans"][kind] = state["replans"].get(kind, 0) + 1

    while queue:
        if steps_done >= MAX_STEPS:
            tracing.log_event("budget_reached", "investigation",
                              {"max_steps": MAX_STEPS})
            break
        step = queue.popleft()
        step_id = step["id"]
        steps_done += 1
        tracing.log_event("step_start", step_id,
                          {"tool": step["tool"], "why": step.get("why"),
                           "n": steps_done})
        result = await execute_with_retry(step, ctx, state)
        state["findings"][step["tool"]] = result
        tracing.log_event("step_end", step_id,
                          {"ok": result.get("ok"), "attempts":
                           state["retries"].get(step_id)})

        # Rule-based replanning: always on, no LLM needed.
        rule_extras = _rule_replan(step, result, state, domain, seen)
        enqueue(rule_extras,
                f"rule after {step['tool']} (ok={result.get('ok')})",
                "rule", step_id)

        # LLM observer: only in live mode, capped.
        if client is not None and llm_replans < MAX_LLM_REPLANS \
                and steps_done < MAX_STEPS:
            llm_replans += 1
            partial = risk.assess(domain, state["findings"])
            state["assessment"] = partial
            summary = _slim_result(step["tool"], result)
            try:
                extra = _sanitize_steps(llm.replan_with_llm(
                    client, model, domain, state, summary), domain)
            except Exception as exc:  # observer is advisory
                extra = []
                tracing.log_event("observer_error", step_id,
                                  {"error": f"{type(exc).__name__}: {exc}"})
            enqueue(extra, f"llm observer after {step['tool']}", "llm",
                    step_id)

    assessment = verify.verify(risk.assess(domain, state["findings"]),
                               state["findings"])
    state["assessment"] = assessment
    if client is not None:
        try:
            state["analyst_summary"] = llm.summarize_with_llm(
                client, model, domain, assessment)
        except Exception:
            state["analyst_summary"] = ""
        tracing.log_event("analyst_summary", "investigation",
                          {"chars": len(state.get("analyst_summary") or "")})
    tracing.log_event("run_end", "investigation",
                      {"score": assessment["score"],
                       "band": assessment["band"],
                       "steps": steps_done})
    state["brief_md"] = brief.render(assessment, state["findings"],
                                     {"run_id": run_id,
                                      "retries": state["retries"],
                                      "mode": mode})
    return state
