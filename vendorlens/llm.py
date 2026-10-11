"""LLM access via the hackathon's LiteLLM gateway (OpenAI-compatible).

Env: LITELLM_API_BASE, LITELLM_API_KEY, LITELLM_MODEL.
The returned client is wrapped by neatlogs so every model call is traced
(model, messages, tool calls, latency, token usage).

The planner and observer prompts are generated from the live ``TOOLS``
registry, so they can never drift from the tools that actually run (P1.1).
"""
from __future__ import annotations

import os

from openai import OpenAI

from . import tracing
from .tools import TOOLS

# Raw-socket tools fail on serverless/restricted networks and have keyless
# HTTP equivalents, so they are listed last with a caveat.
_RAW_SOCKET = {"dns_lookup", "whois_lookup"}


def _tool_lines() -> str:
    ordered = sorted(TOOLS, key=lambda n: (n in _RAW_SOCKET, n))
    lines = []
    for name in ordered:
        desc = getattr(TOOLS[name], "DESCRIPTION", "").split(". ")[0]
        suffix = " (raw-socket, often blocked; prefer keyless HTTP tools)" \
            if name in _RAW_SOCKET else ""
        lines.append(f"- {name}: {desc}{suffix}")
    return "\n".join(lines)


def plan_system_text() -> str:
    return f"""You plan vendor due-diligence OSINT investigations.
Available tools (name: what it does). Use the keyless HTTP tools; the
raw-socket tools are often blocked on servers, so only use them last if needed:
{_tool_lines()}

Reply with JSON only: {{"steps": [{{"id": "s1", "tool": "<name>",
"args": {{"domain": "<domain>"}}, "why": "<one line>"}}]}}.
Order cheap, high-signal tools first. 4-8 steps."""


def observer_system_text() -> str:
    return f"""You observe an in-progress OSINT investigation and decide the
single most useful next step, if any.
Available tools (name: what it does):
{_tool_lines()}

Given the last result and the signals found so far, reply JSON only:
{{"steps": [...]}} with the same step schema, or {{"steps": []}} when nothing
follow-up-worthy happened. Never repeat a (tool, args) already completed."""


PLAN_SYSTEM = plan_system_text()
OBSERVER_SYSTEM = observer_system_text()


def get_client():
    base = os.environ.get("LITELLM_API_BASE", "").strip()
    key = os.environ.get("LITELLM_API_KEY", "").strip()
    model = os.environ.get("LITELLM_MODEL", "").strip() or "claude-haiku"
    if not base or not key:
        raise RuntimeError(
            "LITELLM_API_BASE / LITELLM_API_KEY not set; "
            "run with --demo (canned data), --no-llm (live tools, fixed plan), "
            "or add the shared hackathon key. "
            "Ollama also works: LITELLM_API_BASE=http://localhost:11434/v1 "
            "with any model name.")
    client = OpenAI(base_url=base, api_key=key)
    return tracing.wrap_client(client), model


def _first_json(raw: str):
    import json
    try:
        return json.loads(raw)
    except Exception:
        pass
    start = raw.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(raw)):
            ch = raw[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        import json
                        return json.loads(raw[start:i + 1])
                    except Exception:
                        return None
    return None


def plan_with_llm(client, model: str, domain: str) -> list[dict]:
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": f"Investigate vendor domain: {domain}"},
        ],
        response_format={"type": "json_object"},
        max_tokens=800,
    )
    raw = r.choices[0].message.content or ""
    plan = _first_json(raw)
    if isinstance(plan, dict):
        return plan.get("steps") or []
    if isinstance(plan, list):
        return plan
    return []


def replan_with_llm(client, model: str, domain: str, state: dict,
                    summary: dict) -> list[dict]:
    """Observer: decide whether the last result warrants a follow-up step.

    ``summary`` is a compact, structured view (not a raw blob): the last
    result's key fields plus the risk signals found so far, so the model can
    actually detect a "surprise" instead of just ok/not-ok.
    """
    import json
    signals = [{"signal": s["signal"], "weight": s["weight"]}
               for s in state.get("assessment", {}).get("signals", [])]
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": OBSERVER_SYSTEM},
            {"role": "user", "content": json.dumps({
                "domain": domain,
                "completed": sorted(state.get("findings", {}).keys()),
                "signals_so_far": signals,
                "last_result": summary,
            })[:4000]},
        ],
        response_format={"type": "json_object"},
        max_tokens=400,
    )
    plan = _first_json(r.choices[0].message.content or "")
    if isinstance(plan, dict):
        return plan.get("steps", [])
    if isinstance(plan, list):
        return plan
    return []


def summarize_with_llm(client, model: str, domain: str,
                       assessment: dict) -> str:
    """Constrained analyst summary. The model may only reference the signal
    ids it is given; any unknown reference is stripped, so the summary can
    never invent evidence that is not in the structured assessment."""
    import json
    listed = [{"id": f"sig{i+1}", "signal": s["signal"],
               "weight": s["weight"], "detail": s["detail"]}
              for i, s in enumerate(assessment.get("signals", []))]
    known = {row["id"] for row in listed}
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content":
                 "You are a diligence analyst. Summarise the brief in 3-5 "
                 "sentences using ONLY the signal ids below, citing as "
                 "[sigN]. If a conclusion is not supported by a listed id, "
                 "do not state it. Reply with plain text, no preamble."},
                {"role": "user", "content": json.dumps({
                    "domain": domain,
                    "score": assessment.get("score"),
                    "band": assessment.get("band"),
                    "signals": listed,
                })},
            ],
            max_tokens=300,
        )
        text = (r.choices[0].message.content or "").strip()
    except Exception:
        return ""
    import re
    cited = set(re.findall(r"\[sig\d+\]", text))
    if any(c.strip("[]") not in known for c in cited):
        text = "\n".join(line for line in text.splitlines()
                         if not re.search(r"\[sig\d+\]", line)) or \
            "See the structured signals."
    return text
