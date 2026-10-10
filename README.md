# VendorLens — AI vendor due-diligence agent

Built for **neatHack 2026** (team `solohackaton`, solo). Give it a company
domain; an AI agent plans an OSINT investigation, executes tools step by
step, recovers from failures, verifies claims, and writes a **cited risk
brief** (score + evidence + sources).

## Architecture

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
     | dns / whois  | |  replans on | |  weighted  |
     | tls / home   | |  surprises  | |  signals   |
     | web search   | +-------------+ +-----+------+
     +--------------+                       |
                                     +-------v-------+
                                     | cited brief   |
                                     | brief.md      |
                                     +---------------+

  Every step -> neatlogs spans (LLM auto-traced) + trace.jsonl evidence
  Every commit -> Entire checkpoint (session context behind the change)
  Business plan -> cfo.ai (pricing, costs, revenue, runway)
  Browser verdict -> jev-web typed-decision model, 100% on-device
```

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in keys (or run --demo with none)

# Full agent run, canned data, no keys needed:
python -m vendorlens acme-cloud-services.example --demo

# Live run (needs LITELLM_* in .env):
python -m vendorlens example-vendor.com

# Artifacts land in runs/<domain>/<timestamp>/ : brief.md, state.json, trace.jsonl
```

## The three mandatory tools (and their roles)

1. **neatlogs** — `vendorlens/tracing.py` follows the official setup guide:
   `neatlogs.init(api_key=...)` once, `neatlogs.wrap(OpenAI())` so every
   planner/observer model call is traced (model, messages, latency, tokens).
   Tool executions are logged as structured events to `trace.jsonl` (evidence).
   Signup is manual: app.neatlogs.com -> Settings -> API keys -> **Project**
   API key (top one, NOT the `nlw_` key) -> `NEATLOGS_API_KEY`.
2. **Entire** — `entire/setup.sh` + `entire/ENTIRE.md`. Run setup, sign in
   with GitHub in the browser, import `warsang/vendorlens`, then commit:
   each commit links to the agent session behind it
   (`entire checkpoint list`, `entire checkpoint explain HEAD`). Include the
   checkpoint link + ID in the submission.
3. **cfo.ai** — `docs/business-plan-inputs.md` has the full inputs (pricing
   tiers, unit economics, revenue scenarios, runway). Sign up at
   https://cfo.ai/neathacks (**a card is required; cancel immediately in
   Settings -> Billing**), paste the inputs, include the resulting plan.

## Demo page (jev-web verdict layer)

`demo/` is a static page: paste vendor homepage text, hit **Assess**, and a
Bekko 17m typed-decision model scores scam risk **in the browser** — zero
network requests after weights load, no text leaves the device.

```bash
cd demo && npm install /home/hatch/workspace/jev-web/jev-web-0.7.2.tgz
npx serve .   # open the page it prints
```

## Evidence checklist (mapped to judging criteria)

| Criterion (weight) | Evidence |
|---|---|
| The agent 30% | `brief.md` + `state.json` from a live run; failure->retry->recovery visible in `trace.jsonl` |
| Use of neatlogs/Entire/cfo.ai 25% | neatlogs trace links (before/after runs); Entire checkpoint link + ID; cfo.ai business plan |
| Demo video 20% | `docs/demo-script.md` — 2:45 outline explicitly covering all three tools |
| Building in public 15% | `docs/build-in-public.md` — drafted #neatHack posts (DRAFTS, need approval) |
| Usefulness/originality 10% | cited risk briefs + on-device private scoring |

## Repo & submission

- Public repo: `warsang/vendorlens` (commits must fall within Oct 10–12).
- Submission: quote post of the official neatlogs X post with team, name,
  project, repo and demo link, in the Oct 12 7:00–11:55 PM IST window.

## Notes on live tools

- `dns_lookup` (UDP/53), `whois_lookup` (TCP/43) and `tls_inspect` (direct
  TCP/443) need unrestricted internet. They fail gracefully (recorded as
  failed steps; the agent continues) in restricted sandboxes.
- `fetch_homepage` and `web_search_reports` use httpx and honor proxy env
  vars. If you hit `Invalid port: ':1]'`, your `no_proxy` contains `[::1]`
  which httpx misparses — override with:
  `export no_proxy='localhost,127.0.0.1,::1,198.19.0.1,198.19.0.2'`.
- `--demo` mode runs the whole loop with canned data and no keys.
