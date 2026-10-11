# Committed example runs

Each folder holds a full run: `brief.md` (the cited risk brief), `state.json`
(every per-step result, retry count and latency), and `trace.jsonl` (the
structured event log). Regenerate with `python examples/_regen.py`.

| Folder | Mode | Expected | How it was produced |
|---|---|---|---|
| `github.com` | live `--no-llm` | LOW | Real OSINT responses, no keys (Crustdata optional) |
| `stripe.com` | live `--no-llm` | LOW | Real OSINT responses, no keys |
| `linear.app` | live `--no-llm` | LOW | Real OSINT responses, no keys |
| `suspicious-acme.example` | `--demo --scenario suspicious` | CRITICAL | Canned; young domain + PhishTank/urlscan listings |
| `legit-acme.example` | `--demo --scenario legit` | LOW | Canned; established + strong posture |
| `young-startup.example` | `--demo --scenario young_startup` | MEDIUM | Canned; the hard borderline case |
| `injected-failure-acme.example` | `--demo --inject-failure ct_logs:2` | CRITICAL | Canned; shows failure->retry->recovery in `trace.jsonl` |

## Reading a brief

- **Verdict** is a 0-100 heuristic score and a band.
- The **Signal** table has a **Layer** (real & established / security posture /
  threat & reputation), a **Confidence** tag (corroborated / single-source /
  contradicted) and **Weight**; every claim cites `[n]` sources.
- **What we could not verify** lists tools that failed or produced no signal.

## Caveats (stated honestly)

- Expected bands are one analyst's labels, not ground truth; see
  `eval/` and `docs/scoring.md` for the offline confusion table and the weight
  rationale. Domain classification is subjective at the boundary.
- The three live examples depend on live third-party responses; a rerun today
  may differ slightly (scan counts, cert counts, registrar). The canned
  scenarios are byte-stable.
- The `--inject-failure` flag is **fault injection** for demoing recovery, not
  a real outage.
- Company domains only; no test data was collected from real people.
