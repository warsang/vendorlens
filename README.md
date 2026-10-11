# VendorLens — AI vendor due-diligence agent

Built solo for **neatHack 2026** (team `solohackaton`). Give it a company
domain; an AI agent plans an OSINT investigation, executes tools step by
step, recovers from failures, verifies claims, and writes a **cited risk
brief** (score + evidence + sources).

## Demo

- **Live demo (public, zero keys):** https://vendorlens-demo.pages.dev —
  paste a vendor's homepage text, hit **Investigate**, and the Bekko 17m
  typed-decision model scores scam risk **in the browser** (zero network
  requests after the ~29 MB of weights load; no text leaves the device).
  Deployed from this repo's `demo/` folder to Cloudflare Pages.
- **Demo video (1:44, covers neatlogs + Entire + cfo.ai):**
  - `docs/demo.mp4` in this repo: https://github.com/warsang/vendorlens/blob/main/docs/demo.mp4
  - release asset: https://github.com/warsang/vendorlens/releases/tag/demo
  - source: `docs/video-slides.html` (the nine scenes the video is built from)
- **Storyboard + timings:** `docs/demo-script.md`

## Agent evidence (run it yourself)

```bash
pip install -r requirements.txt
python -m vendorlens acme-cloud-services.example --demo   # canned, no keys
python -m vendorlens linear.app                            # live LLM-planned run (needs LITELLM_*)
```

Committed run artifacts (brief + state + trace for every investigation):

| Run | What it proves |
|---|---|
| [`runs/linear.app/20261011T215820Z`](runs/linear.app/20261011T215820Z/brief.md) | Live LLM-planned run: planner picks 6 tools, brief written, score 2/100 LOW with every signal cited |
| [`runs/acme-cloud-services.example/20261011T215709Z`](runs/acme-cloud-services.example/20261011T215709Z/brief.md) | The canned run the public demo page replays: MEDIUM 48/100, 9 tools, cited signals |
| [`runs/amazon.com/20261011T203036Z`](runs/amazon.com/20261011T203036Z/brief.md) | Failure and recovery: `tool_retry` x3 with backoff in [`trace.jsonl`](runs/amazon.com/20261011T203036Z/trace.jsonl), run continues, brief still written |
| [`runs/example.com/20261011T091433Z`](runs/example.com/20261011T091433Z/trace.jsonl) | Key-less Crustdata call fails 3x, agent records the failure and continues |

Architecture:

```
                     +-------------------+
                     |   planner (LLM)   |  JSON plan: 4-8 tool steps,
                     +--------+----------+  cheapest high-signal first
                              |
                     +--------v----------+
                     |  executor + state |  persistent state dict across steps
                     +--------+----------+  per-step retry w/ backoff
                              |
               +--------------+--------------+
               |              |              |
      +--------v-----+ +------v------+ +-----v------+
      |    tools     | |  observer   | |   risk     |
      | crustdata    | |  (LLM)      | |  scoring   |
      | dns / rdap   | |  replans on | |  weighted  |
      | tls / ct     | |  surprises  | |  signals   |
      +--------------+ +-------------+ +-----+------+
                                              |
                                      +-------v-------+
                                      | cited brief   |  brief.md
                                      +---------------+

   Every step -> neatlogs spans (LLM auto-traced) + trace.jsonl evidence
   Every commit -> Entire checkpoint (session context behind the change)
   Business plan -> cfo.ai (pricing, costs, revenue, runway)
   Browser verdict -> jev-web typed-decision model, 100% on-device
```

## The three mandatory tools

### 1. neatlogs — observability for the agent

`vendorlens/tracing.py` follows the official setup guide:
`neatlogs.init(api_key=...)` once, `neatlogs.wrap(OpenAI())` so every
planner/observer model call is traced (model, messages, latency, tokens),
and one root `WORKFLOW` span named `vendorlens-investigation` per run
([`vendorlens/__main__.py:26`](vendorlens/__main__.py)). Tool executions
are logged as structured events to `runs/<domain>/<ts>/trace.jsonl`.

- **Dashboard:** https://app.neatlogs.com (project `vendorlens-investigation`)
- **Live traced runs:** committed above under `runs/` (`neatlogs live
  tracing: on` in every live run's output; `trace.jsonl` is the local
  mirror of the same events)
- Retry/backoff and tool failures are `tool_retry` events in the trace:
  `runs/amazon.com/20261011T203036Z/trace.jsonl`

### 2. Entire — every commit tied to its agent session

The repo runs `entire enable --agent opencode` (hooks in `.git/hooks/`,
plugin in `.opencode/plugins/`), so each commit captures the agent session
that produced it.

- **Checkpoint (commit 4ef39f1):** https://entire.io/gh/warsang/vendorlens/commit/4ef39f1
- **Checkpoint ID:** see `entire checkpoint list` output ([`entire/ENTIRE.md`](entire/ENTIRE.md)
  has the exact steps; checkpoints sync to `origin` and are visible via the link above)

### 3. cfo.ai — the business plan

Planned as a SaaS in cfo.ai (https://cfo.ai/neathacks):

- **Pricing:** Starter $49/mo (50 investigations), Team $199/mo (500 + API +
  Slack alerts), Enterprise custom (SSO, audit log, DPA)
- **Costs:** ~$0.04 blended model cost per investigation, ~$0.10 Crustdata
  enrichment on Team+, gross margin 80-85%, burn ~$16k/mo at base scenario
- **Revenue (year 1):** conservative $288k ARR, base ~$1.0M ARR, optimistic
  $2.7M ARR
- **Runway:** $250k pre-seed, ~15 months to profitability at ~450 paying teams
- Full inputs: [`docs/business-plan-inputs.md`](docs/business-plan-inputs.md);
  exported plan: [`docs/business-plan.pdf`](docs/business-plan.pdf)

## Claim-by-claim evidence

Every README claim maps to a file, a commit or a trace a judge can check:

| Claim | Evidence |
|---|---|
| The agent plans an OSINT investigation, executes step by step, recovers from failures, verifies claims and writes a cited brief | `vendorlens/agent.py:83` (run loop), `vendorlens/brief.py` (cited render), retry+fallback in `vendorlens/agent.py:62` and per-tool `except` returns (e.g. `vendorlens/tools/rdap_lookup.py:97`); failure run: `runs/amazon.com/20261011T203036Z/trace.jsonl` |
| The project uses neatlogs to trace all planner and observer model calls and logs tool executions as structured events in trace.jsonl | `vendorlens/tracing.py:39` (init), `vendorlens/llm.py:28` (wrapped client), `vendorlens/tracing.py:76` (trace.jsonl events); proof run: `runs/linear.app/20261011T215820Z` |
| Each git commit is linked to the agent session via Entire checkpoints | Entire hooks enabled (`entire status`), plugin `.opencode/plugins/entire.ts`, checkpoint link above |
| The project integrates cfo.ai to generate a business plan from provided inputs | `docs/business-plan-inputs.md` (the inputs), `docs/business-plan.pdf` (the exported plan), https://cfo.ai/neathacks |
| The demo page runs a typed-decision model in the browser that scores scam risk with no network requests after weights load | `demo/index.html` (on-device `getDecider` + `decide()`), live proof: https://vendorlens-demo.pages.dev ("bekko-system-one-v0-17m · Nms · zero network" tag renders after weights load) |
| DNS, RDAP and TLS tools fail gracefully when network is restricted, allowing the agent to continue | every tool returns `{"ok": False, "error": ...}` instead of raising (e.g. `vendorlens/tools/rdap_lookup.py:97`, `vendorlens/tools/doh_dns.py`, `vendorlens/tools/tls_tool.py`); the executor retries then records the failure: `vendorlens/agent.py:62-80` |
| `--demo` runs the full loop with canned data and requires no API keys | `DEMO_DATA` canned responses in each tool module (e.g. `vendorlens/tools/rdap_lookup.py:15`), selected by the demo context in `vendorlens/agent.py:99`; run proof: `runs/acme-cloud-services.example/20261011T215709Z` |

## Building in public (#neatHack)

Drafted posts live in [`docs/build-in-public.md`](docs/build-in-public.md).
Posted from X before the Oct 12 7:00-11:55 PM IST submission window; links:

1. Kickoff (Sat): posted from @Theodore's account, thread link to be added here on post.
2. Mid-hack update (retry/backoff in the trace): link to be added here on post.
3. Submission post (repo + demo + evidence): link to be added here on post.

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env    # fill in keys (optional: --demo needs none)

python -m vendorlens <domain>            # full LLM planning (needs LITELLM_*)
python -m vendorlens <domain> --no-llm   # live tools, deterministic plan
python -m vendorlens <domain> --demo     # canned data, zero keys
```

Artifacts land in `runs/<domain>/<timestamp>/`: `brief.md`, `state.json`,
`trace.jsonl`.

## Notes on live tools

- `dns_lookup` (UDP/53), `whois_lookup` (TCP/43), `rdap_lookup` (HTTPS) and
  `tls_inspect` (direct TCP/443) need unrestricted internet. They fail
  gracefully (recorded as failed steps; the agent continues) in restricted
  sandboxes.
- `fetch_homepage` and `web_search_reports` use httpx and honor proxy env
  vars. If you hit `Invalid port: ':1]'`, your `no_proxy` contains `[::1]`
  which httpx misparses — override with:
  `export no_proxy='localhost,127.0.0.1,::1,198.19.0.1,198.19.0.2'`.
- Local Ollama also works: `LITELLM_API_BASE=http://localhost:11434/v1`.

## Submission

- Public repo: `warsang/vendorlens` (commits Oct 10-12, 2026)
- Submission: quote post of the official neatlogs X post with team, name,
  project, repo, demo link, Entire checkpoint link + ID, cfo.ai plan and
  neatlogs trace links.
