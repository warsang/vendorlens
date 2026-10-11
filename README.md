# VendorLens: AI vendor due-diligence agent

Built solo for **neatHack 2026** (team `solohackaton`). Give it a company
domain; an AI agent plans an OSINT investigation, executes tools step by
step, adapts and recovers from failures, verifies claims across sources, and
writes a **cited risk brief**: a 0-100 score, layered evidence, a confidence
tag per claim, and links to the public source behind every signal.

## Demo

- **Live demo page (public, zero keys):** https://vendorlens-demo.pages.dev
  Open it, hit **Load example** to render a committed brief, and the Bekko
  17m typed-decision model scores the text **in the browser** (zero network
  after the ~29 MB of weights load; no text leaves the device).
- **Demo video (covers neatlogs + Entire + cfo.ai):**
  - `docs/demo.mp4`: https://github.com/warsang/vendorlens/blob/main/docs/demo.mp4
    (earlier cut, recorded on an earlier canned dataset; the current `--demo`
    scores CRITICAL, see `examples/suspicious-acme.example/brief.md`)
  - slide source: `docs/video-slides.html`; final recording script:
    `docs/demo-script.md`
- **Storyboard + timings:** `docs/demo-script.md`

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # keys optional; --demo needs none

python -m vendorlens acme-cloud-services.example --demo            # canned, zero keys
python -m vendorlens stripe.com --no-llm                          # live tools, no LLM key
python -m vendorlens example-vendor.com                           # full LLM-planned run (needs LITELLM_*)
```

Flags: `--scenario <suspicious|legit|young_startup>` for canned stories,
`--inject-failure <tool>[:n]` to demo failure -> retry -> recovery, and
`--tag <name>` to label a run. Artifacts land in
`runs/<domain>/<timestamp>/`: `brief.md`, `state.json`, `trace.jsonl`.

## Evidence (committed, verifiable)

Real briefs + traces live in [`examples/`](examples/README.md):

| Example | Mode | Verdict | What it proves |
|---|---|---|---|
| [`examples/stripe.com`](examples/stripe.com/brief.md) | live | LOW 0/100 | Established vendor: long cert history, DMARC enforced, HSTS/CSP, all cited |
| [`examples/github.com`](examples/github.com/brief.md) | live | LOW 0/100 | Same, from live OSINT with no keys |
| [`examples/suspicious-acme.example`](examples/suspicious-acme.example/brief.md) | canned | CRITICAL 100/100 | Young domain + PhishTank/urlscan listings + self-signed cert + scam copy |
| [`examples/young-startup.example`](examples/young-startup.example/brief.md) | canned | MEDIUM 29/100 | The hard borderline case, honestly scored |
| [`examples/injected-failure-acme.example`](examples/injected-failure-acme.example/trace.jsonl) | canned | CRITICAL | Failure -> retry -> recovery visible in `trace.jsonl` |

Offline eval (re-scores the committed runs, no network):

```bash
python -m vendorlens.eval       # confusion table + accuracy over examples/
python -m pytest                # 60+ unit/regression tests
python examples/_regen.py       # regenerate the committed examples
```

Every signal, weight and rationale is listed in [`docs/scoring.md`](docs/scoring.md).

## How it works

```
                     +-------------------+   JSON plan generated from the live
                     |   planner (LLM)   |   TOOLS registry (falls back to a
                     +--------+----------+   deterministic 8-tool plan)
                              |
                     +--------v----------+
                     |  executor + state |   one retry layer: only transient
                     +--------+----------+   errors retried (429/5xx/timeout),
                              |               deterministic failures recorded once
        +---------------------+---------------------+
        |                     |                     |
 +------v------+       +-------v-------+      +------v------+
 | 11 tools    |       |  observer     |      |  risk       |
 | rdap/doh    |       |  LLM + rules  |      |  weighted   |
 | ct/urlscan  |       |  capped+dedupe|      |  + verify   |
 | phishtank   |       |  replanning   |      |  3 layers   |
 | homepage    |       +---------------+      +------+------+
 | crustdata   |                                |
 +-------------+                         +------v------+
                                       |  cited brief |
                                       |  brief.md    |
                                       +-------------+

 Every step -> neatlogs WORKFLOW + nested TOOL spans (LLM calls auto-traced)
               + trace.jsonl evidence
 Every commit -> Entire checkpoint (the agent session behind the change)
 Business plan -> cfo.ai (pricing, costs, revenue, runway, breakeven)
 Browser verdict -> jev-web typed-decision model, 100% on-device
```

Three data layers, so a buyer reads the brief as answers plus a
disqualifier watch:

1. **real & established** -- is this domain a real, operating business?
   (registration age, resolution + mail, SPF/DMARC, certificate history,
   company record, privacy/terms pages)
2. **security posture** -- is the vendor's hygiene mature? (TLS, HSTS/CSP,
   security.txt, DMARC enforcement)
3. **threat & reputation** -- active abuse signals. (PhishTank, urlscan
   verdicts, scam copy, vendor-scoped negative reports)

## The three mandatory tools

### 1. neatlogs (observability)

`vendorlens/tracing.py` follows the official setup guide: `neatlogs.init`
once, `neatlogs.wrap(OpenAI())` so every planner/observer/analyst call is
traced (model, messages, latency, tokens), one root `WORKFLOW` span per run
with a nested child span per tool step. Tool executions also land as
structured events in `runs/<domain>/<ts>/trace.jsonl` (the local mirror).
Signup is manual; the Project API key goes in `NEATLOGS_API_KEY`.
Dashboard project: `vendorlens-investigation`. Committed live runs were made
with `neatlogs live tracing: on`.

### 2. Entire (checkpoints)

The repo runs `entire enable --agent opencode` (hooks in `.git/hooks/`), so
each commit captures the agent session that produced it. See
[`entire/ENTIRE.md`](entire/ENTIRE.md) for setup; checkpoints show with
`entire checkpoint list` and `entire checkpoint explain HEAD`.

### 3. cfo.ai (business plan)

Inputs are in [`docs/business-plan-inputs.md`](docs/business-plan-inputs.md)
(margins, unit economics, runway and breakeven are internally consistent).
Export the plan at https://cfo.ai/neathacks and include it in the submission.

## Honest limitations

- Weights are expert-chosen, not learned; the offline eval scores 7 labelled
  cached runs and domain classification is subjective near the LOW/MEDIUM
  boundary. See `docs/scoring.md`.
- `dns_lookup` (UDP/53), `whois_lookup` (TCP/43) and `tls_inspect` (direct
  TCP/443) need unrestricted internet and fail gracefully in restricted
  sandboxes; `doh_dns` and `rdap_lookup` are their keyless HTTPS successors.
- `httpx` honors proxy env vars. If you hit `Invalid port: ':1]'`, your
  `no_proxy` contains `[::1]`, which httpx misparses; override with
  `export no_proxy='localhost,127.0.0.1,::1,198.19.0.1,198.19.0.2'`.
- `--inject-failure` is labelled fault injection for demoing recovery, not a
  real outage.
- The public endpoint treats `x-api-key` as a **public client token** (rate
  attribution), not authentication; protection is external rate limiting, a
  spend budget, and a pinned `ALLOWED_ORIGIN`.

## Building in public

Drafted posts live in [`docs/build-in-public.md`](docs/build-in-public.md);
posting is human-approved only.

## License

MIT, see [`LICENSE`](LICENSE).

## Submission

- Public repo: `warsang/vendorlens` (commits Oct 10-12, 2026).
- Submission: quote post of the official neatlogs X post with team
  (`solohackaton`), name, project, repo, demo link, Entire checkpoint
  link + ID, cfo.ai plan, and neatlogs trace links, inside the Oct 12
  7:00-11:55 PM IST window.
