"""CLI: python -m vendorlens <domain> [--demo] [--no-llm] [--out DIR]
[--scenario NAME] [--inject-failure TOOL[:N]] [--tag NAME]"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _parse_inject(specs) -> dict:
    inject: dict = {}
    for spec in specs or []:
        tool, _, n = spec.partition(":")
        tool = tool.strip()
        if not tool:
            continue
        try:
            inject[tool] = max(1, int(n))
        except ValueError:
            inject[tool] = 1
    return inject


def main() -> int:
    ap = argparse.ArgumentParser(description="VendorLens vendor OSINT agent")
    ap.add_argument("domain", help="vendor domain to investigate")
    ap.add_argument("--demo", action="store_true",
                    help="run with canned data (no API keys needed)")
    ap.add_argument("--no-llm", action="store_true",
                    help="live tools with a deterministic plan (no LLM key "
                         "needed)")
    ap.add_argument("--scenario", default=None,
                    help="canned story for --demo: suspicious | legit | "
                         "young_startup (default suspicious)")
    ap.add_argument("--inject-failure", action="append", default=[],
                    metavar="TOOL[:N]",
                    help="fault injection: fail the first N attempts of a "
                         "tool (default 1) to show failure->retry->recovery")
    ap.add_argument("--tag", default=None,
                    help="label the run (baseline|improved) for before/after")
    ap.add_argument("--out", default="runs",
                    help="output directory for run artifacts")
    args = ap.parse_args()

    from . import agent, tracing

    live_tracing = tracing.init_tracing("vendorlens-investigation")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = args.domain.replace("/", "_")
    run_dir = Path(args.out) / slug / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    run_id = uuid.uuid4().hex[:8]
    tracing.set_trace_file(run_dir / "trace.jsonl", run_id)

    inject = _parse_inject(args.inject_failure)
    with tracing.workflow("vendorlens-investigation", domain=args.domain,
                           mode="demo" if args.demo else
                           ("no-llm" if args.no_llm else "live"),
                           tag=args.tag or ""):
        state = asyncio.run(
            agent.run_investigation(args.domain, demo=args.demo,
                                    run_id=run_id, no_llm=args.no_llm,
                                    scenario=args.scenario, inject=inject,
                                    tag=args.tag))

    (run_dir / "brief.md").write_text(state["brief_md"], encoding="utf-8")
    (run_dir / "state.json").write_text(
        json.dumps({k: v for k, v in state.items() if k != "brief_md"},
                   indent=2, default=str), encoding="utf-8")

    print(state["brief_md"])
    if state.get("analyst_summary"):
        print("\n## Analyst summary\n\n" + state["analyst_summary"])
    print(f"artifacts: {run_dir}")
    print(f"neatlogs live tracing: {'on' if live_tracing else 'off (no key)'}")
    tracing.flush()
    tracing.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
