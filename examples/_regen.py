#!/usr/bin/env python
"""Regenerate the committed example runs under examples/.

Provenance:
  - the three legit vendors are LIVE runs (real OSINT responses, --no-llm);
    they need network + (optionally) CRUSTDATA_API_KEY to reproduce.
  - the suspicious / young-startup / injected-failure runs use the canned
    --demo scenarios, so they are fully reproducible with zero keys/network.

Usage:
    python examples/_regen.py            # writes examples/<name>/{brief.md,state.json,trace.jsonl}
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vendorlens import agent, tracing  # noqa: E402

EX = Path(__file__).resolve().parent

# (dir name, domain, mode kwargs)
RUNS = [
    ("github.com", "github.com", {"no_llm": True}),
    ("stripe.com", "stripe.com", {"no_llm": True}),
    ("linear.app", "linear.app", {"no_llm": True}),
    ("suspicious-acme.example", "acme-cloud-services.example",
     {"demo": True, "scenario": "suspicious"}),
    ("young-startup.example", "acme-cloud-services.example",
     {"demo": True, "scenario": "young_startup"}),
    ("legit-acme.example", "acme-cloud-services.example",
     {"demo": True, "scenario": "legit"}),
    ("injected-failure-acme.example", "acme-cloud-services.example",
     {"demo": True, "scenario": "suspicious", "inject": {"ct_logs": 2}}),
]


def run_one(name: str, domain: str, kwargs: dict) -> dict:
    out = EX / name
    out.mkdir(parents=True, exist_ok=True)
    tracing.init_tracing("vendorlens-investigation")
    tracing.set_trace_file(out / "trace.jsonl", name[:8])
    tracing.log_event("example_regen", name,
                      {"domain": domain, "kwargs": sorted(kwargs)})
    try:
        state = asyncio.run(agent.run_investigation(domain, **kwargs))
    finally:
        tracing.flush()
        tracing.shutdown()
        tracing.set_trace_file(None, "")
    (out / "brief.md").write_text(state["brief_md"], encoding="utf-8")
    (out / "state.json").write_text(
        json.dumps({k: v for k, v in state.items() if k != "brief_md"},
                   indent=2, default=str), encoding="utf-8")
    a = state["assessment"]
    return {"name": name, "domain": domain, "band": a["band"],
            "score": a["score"], "signals": len(a["signals"]),
            "mode": state["mode"]}


def main() -> int:
    summary = []
    for name, domain, kwargs in RUNS:
        row = run_one(name, domain, kwargs)
        summary.append(row)
        print(f"{name:32s} {row['band']:9s} {row['score']:>3} "
              f"signals={row['signals']} mode={row['mode']}")
    (EX / "index.json").write_text(json.dumps(summary, indent=2),
                                   encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
