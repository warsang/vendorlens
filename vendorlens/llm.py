"""LLM access via the hackathon's LiteLLM gateway (OpenAI-compatible).

Env: LITELLM_API_BASE, LITELLM_API_KEY, LITELLM_MODEL.
The returned client is wrapped by neatlogs so every model call is traced
(model, messages, tool calls, latency, token usage).
"""
from __future__ import annotations

import os

from openai import OpenAI

from . import tracing


def get_client():
    base = os.environ.get("LITELLM_API_BASE", "").strip()
    key = os.environ.get("LITELLM_API_KEY", "").strip()
    model = os.environ.get("LITELLM_MODEL", "").strip() or "claude-haiku"
    if not base or not key:
        raise RuntimeError(
            "LITELLM_API_BASE / LITELLM_API_KEY not set; "
            "run with --demo or add the shared hackathon key.")
    client = OpenAI(base_url=base, api_key=key)
    return tracing.wrap_client(client), model


PLAN_SYSTEM = """You plan vendor due-diligence OSINT investigations.
Available tools (name: what it does):
- crustdata_enrich: company firmographics by domain
- dns_lookup: A, MX, TXT records
- whois_lookup: domain age and registrar
- tls_inspect: certificate expiry and issuer
- fetch_homepage: homepage text for scam-signal analysis
- web_search_reports: web search for scam reports and reviews

Reply with JSON only: {"steps": [{"id": "s1", "tool": "<name>",
"args": {"domain": "<domain>"}, "why": "<one line>"}]}.
Order cheap, high-signal tools first. 4-8 steps."""


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
    import json
    plan = json.loads(r.choices[0].message.content)
    return plan["steps"]


def replan_with_llm(client, model: str, domain: str, state: dict,
                    last_result: dict) -> list[dict]:
    """Observer: decide whether the last result warrants follow-up steps."""
    import json
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content":
             "You observe an OSINT investigation. Given the last tool result, "
             "decide if follow-up steps are needed. Reply JSON only: "
             '{"steps": [...]} with the same step schema, or {"steps": []}.'},
            {"role": "user", "content": json.dumps({
                "domain": domain,
                "completed": list(state["findings"].keys()),
                "last_result": last_result,
            })[:4000]},
        ],
        response_format={"type": "json_object"},
        max_tokens=400,
    )
    return json.loads(r.choices[0].message.content).get("steps", [])
