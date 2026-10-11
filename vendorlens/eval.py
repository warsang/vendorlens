"""Offline evaluation: re-score committed cached runs and print a confusion table.

Runs entirely from the findings stored in ``examples/*/state.json`` (no
network, no keys), so it is deterministic and safe in CI. Expected bands come
from ``eval/domains.csv``; those labels are one analyst's judgement, not ground
truth, and domain classification is subjective at the LOW/MEDIUM boundary.

Usage:
    python -m vendorlens.eval
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from . import risk, verify

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
DOMAINS = Path(__file__).resolve().parent.parent / "eval" / "domains.csv"
BANDS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _load_expected() -> dict:
    out = {}
    with open(DOMAINS, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["key"]] = row["expected_band"].strip().upper()
    return out


def _load_findings() -> list[tuple[str, str, dict]]:
    runs = []
    for state_path in sorted(EXAMPLES.glob("*/state.json")):
        key = state_path.parent.name
        data = json.loads(state_path.read_text(encoding="utf-8"))
        runs.append((key, data.get("domain", key), data.get("findings", {})))
    return runs


def _collapse(band: str) -> str:
    # HIGH and CRITICAL both mean "do not deal with them yet".
    return "HIGH+" if band in ("HIGH", "CRITICAL") else band


def main() -> int:
    expected = _load_expected()
    runs = _load_findings()
    correct = 0
    scored = 0
    confusion: dict = defaultdict(lambda: defaultdict(int))
    rows = []
    for key, domain, findings in runs:
        if key not in expected or not findings:
            continue
        assessment = verify.verify(risk.assess(domain, findings), findings)
        got, exp = assessment["band"], expected[key]
        rows.append((key, domain, exp, got, assessment["score"]))
        confusion[exp][got] += 1
        scored += 1
        if _collapse(got) == _collapse(exp):
            correct += 1

    print("VendorLens offline eval (cached runs, no network)\n")
    print(f"{'example':32s} {'domain':30s} {'expected':9s} {'pred':9s} score")
    print("-" * 92)
    for key, domain, exp, got, score in rows:
        flag = "" if _collapse(exp) == _collapse(got) else "  <-- miss"
        print(f"{key:32s} {domain:30s} {exp:9s} {got:9s} {score}{flag}")

    print("\nConfusion (expected -> predicted):")
    print("            " + "".join(f"{b:>10s}" for b in BANDS))
    for exp in BANDS:
        cells = "".join(f"{confusion[exp][b]:>10d}" for b in BANDS)
        print(f"  {exp:9s} {cells}")

    if scored:
        print(f"\nsample size: {scored}  "
              f"exact: {sum(r[2] == r[3] for r in rows)}/{scored}  "
              f"band-aware (HIGH+ collapsed): {correct}/{scored}")
    print("\nNote: labels are one analyst's judgement; the LOW/MEDIUM boundary "
          "is subjective. See docs/scoring.md for weights/rationale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
