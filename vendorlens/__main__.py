"""CLI: python -m vendorlens <domain> [--demo] [--out DIR]"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="VendorLens vendor OSINT agent")
    ap.add_argument("domain", help="vendor domain to investigate")
    ap.add_argument("--demo", action="store_true",
                    help="run with canned data (no API keys needed)")
    ap.add_argument("--out", default="runs",
                    help="output directory for run artifacts")
    args = ap.parse_args()

    from . import agent, tracing

    live_tracing = tracing.init_tracing("vendorlens-investigation")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.out) / args.domain / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    import uuid
    run_id = uuid.uuid4().hex[:8]
    tracing.set_trace_file(run_dir / "trace.jsonl", run_id)

    state = asyncio.run(
        agent.run_investigation(args.domain, demo=args.demo, run_id=run_id))

    (run_dir / "brief.md").write_text(state["brief_md"], encoding="utf-8")
    (run_dir / "state.json").write_text(
        json.dumps({k: v for k, v in state.items() if k != "brief_md"},
                   indent=2, default=str), encoding="utf-8")

    print(state["brief_md"])
    print(f"artifacts: {run_dir}")
    print(f"neatlogs live tracing: {'on' if live_tracing else 'off (no key)'}")
    tracing.flush()
    tracing.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
