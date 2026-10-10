"""Markdown risk-brief renderer. Every claim cites its source."""
from __future__ import annotations

from datetime import datetime, timezone


def render(assessment: dict, findings: dict, run_meta: dict) -> str:
    a = assessment
    lines = [
        f"# VendorLens risk brief: {a['domain']}",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()} by VendorLens "
        f"(neatHack 2026, team solohackaton). "
        f"Run {run_meta.get('run_id', 'n/a')}._",
        "",
        f"## Verdict: {a['band']} ({a['score']}/100)",
        "",
        "| Signal | Weight | Detail | Sources |",
        "| --- | --- | --- | --- |",
    ]
    for s in a["signals"]:
        srcs = ", ".join(f"[{i+1}]" for i in range(len(s["sources"])))
        lines.append(f"| {s['signal']} | {s['weight']:+d} | {s['detail']} "
                     f"| {srcs} |")
    lines += ["", "## Sources"]
    for i, src in enumerate(a["sources"], 1):
        lines.append(f"[{i}] {src}")
    lines += ["", "## Tool results"]
    for name, res in findings.items():
        status = "ok" if res.get("ok") else "FAILED"
        lines.append(f"- **{name}**: {status}")
        if not res.get("ok"):
            lines.append(f"  - error: {res.get('error')}")
    lines += [
        "",
        "## Methodology",
        "",
        "An AI agent planned an OSINT investigation, executed six tools step "
        "by step (company enrichment, DNS, WHOIS, TLS, homepage analysis, "
        "web search), retried failures with backoff, and combined the "
        "outputs into weighted risk signals. Every claim above cites the "
        "tool and source behind it. Scores are heuristic, not financial "
        "advice; verify before acting.",
    ]
    return "\n".join(lines) + "\n"
