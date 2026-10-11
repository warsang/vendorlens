"""Markdown risk-brief renderer. Every claim cites its source.

Citations are resolved against the global, sorted source list, so a signal's
[N] markers point at the exact sources that produced it (not a per-signal
count that disagrees with the list). URL sources are rendered as links.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _cite_marker(n: int) -> str:
    return f"[{n}]"


def _render_source(i: int, src: str) -> str:
    if src.startswith("http://") or src.startswith("https://"):
        return f"[{i}] <{src}>"
    return f"[{i}] {src}"


def _confidence_tag(s: dict) -> str:
    v = s.get("verification", "")
    return {"corroborated": "corroborated",
            "single_source": "single-source",
            "contradicted": "contradicted"}.get(v, v or "single-source")


def render(assessment: dict, findings: dict, run_meta: dict) -> str:
    a = assessment
    index = {src: n for n, src in enumerate(a["sources"], 1)}

    header = [
        f"# VendorLens risk brief: {a['domain']}",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()} by VendorLens "
        f"(neatHack 2026, team solohackaton). "
        f"Run {run_meta.get('run_id', 'n/a')}._",
        "",
        f"## Verdict: {a['band']} ({a['score']}/100)",
        "",
        "| Signal | Layer | Confidence | Weight | Detail | Sources |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for s in a["signals"]:
        cites = []
        for src in s.get("sources", []):
            n = index.get(src)
            if n is not None and _cite_marker(n) not in cites:
                cites.append(_cite_marker(n))
        srcs = ", ".join(cites) or "n/a"
        header.append(
            f"| {s['signal']} | {s.get('layer', '')} "
            f"| {_confidence_tag(s)} | {s['weight']:+d} | {s['detail']} "
            f"| {srcs} |")

    lines = [*header, "", "## Sources"]
    lines += [_render_source(i, src) for i, src in enumerate(a["sources"], 1)]

    lines += ["", "## Tool results"]
    for name, res in findings.items():
        status = "ok" if res.get("ok") else "FAILED"
        lines.append(f"- **{name}**: {status}")
        if not res.get("ok"):
            lines.append(f"  - error: {res.get('error')}")

    could_not = a.get("could_not_verify") or []
    if could_not:
        lines += ["", "## What we could not verify"]
        for c in could_not:
            lines.append(f"- **{c.get('item')}**: {c.get('reason')}")

    for note in (a.get("notes") or []):
        lines += ["", f"> {note}"]

    # Methodology: derived from what actually ran, not a fixed sentence.
    tool_names = sorted(findings.keys())
    ok_tools = [n for n in tool_names if findings[n].get("ok")]
    failed_tools = [n for n in tool_names if not findings[n].get("ok")]
    retries = run_meta.get("retries") or {}
    retried = [k for k, v in retries.items() if v and v > 1]
    retry_clause = (f" {len(retried)} step(s) failed transiently and "
                    f"recovered after backoff ({', '.join(retried)})."
                    if retried else " No step needed a retry.")
    method = (
        f"An AI agent planned and executed a step-by-step OSINT "
        f"investigation using {len(tool_names)} tools ({', '.join(tool_names)}"
        f"). {len(ok_tools)} succeeded and {len(failed_tools)} failed; "
        f"failures are recorded, never fatal.{retry_clause} "
        f"Outputs were combined into weighted risk signals across three "
        f"layers (is it real and established, is its security posture mature, "
        f"are there active abuse signals). Every claim cites the tool and "
        f"source behind it and is tagged corroborated, single-source or "
        f"contradicted. Scores are heuristic, not financial advice; verify "
        f"before acting.")

    lines += ["", "## Methodology", "", method]
    return "\n".join(lines) + "\n"
