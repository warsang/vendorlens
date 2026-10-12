# Archived run evidence (raw trace + state)

These three folders are **raw archives** from earlier live runs on Oct 11,
kept because the README's before/after notes and the neatlogs screenshot cite
them. Each contains `trace.jsonl` (the structured event log) and `state.json`
(the per-step findings), which is where every cited number comes from.

The **corrected briefs** (with citations resolved against the global source
index, layers, and confidence tags) live under [`../examples/`](../examples/).
The pre-fix `brief.md` files from these runs are intentionally not committed:
they predate the P0.1 citation fix and would show the old "[1] for every
signal" rendering.

Archived runs:

- `example.com/20261011T091433Z` — `crustdata_enrich` fails with no API key;
  the run still completes (graceful degradation).
- `amazon.com/20261011T203036Z` — a flaky feed is retried with fixed sleeps,
  including a deterministic "feed too large" error (pre-P1.3 behaviour).
- `linear.app/20261011T215820Z` — a live LLM-planned run; source of the
  neatlogs trace screenshot at `docs/neatlogs-trace-evidence.jpg`.

`runs/` is gitignored for new runs (see `.gitignore`); only these archived
evidence folders are tracked.
