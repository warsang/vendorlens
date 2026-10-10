# Agent onboarding — VendorLens

You just cloned `warsang/vendorlens`. This doc gets you from zero to a
working, fully-wired repo. Human (Theodore) handles browser/OAuth steps;
you do everything else.

## 1. Environment

```bash
./setup.sh          # interactive: writes chmod-600 .env (gitignored, never commit it)
```

Keys (all in `.env`, never in code):

| Var | Where the human gets it |
|---|---|
| `NEATLOGS_API_KEY` | app.neatlogs.com → project → Settings → API keys (top key, not `nlw_`) |
| `CRUSTDATA_API_KEY` | app.crustdata.com → dashboard home → API key card → Show API key |
| `LITELLM_API_BASE` / `LITELLM_API_KEY` / `LITELLM_MODEL` | Hackathon shared key (check-in email / Discord). Optional |
| Local LLM alternative | `LITELLM_API_BASE=http://localhost:11434/v1` (Ollama), any model name |

No LLM key at all? Run with `--no-llm` (live tools, deterministic plan).
`--demo` runs everything on canned data with zero keys.

## 2. Run it

```bash
python -m vendorlens <domain> --no-llm     # no LLM key needed
python -m vendorlens <domain>              # full LLM planning (needs LITELLM_*)
python -m vendorlens acme.example --demo   # canned, no keys
```

Artifacts: `runs/<domain>/<ts>/` → `brief.md`, `state.json`, `trace.jsonl`.
neatlogs tracing is automatic when `NEATLOGS_API_KEY` is set; each run is
one root `WORKFLOW` trace named `vendorlens-investigation`.

Sandbox note: if `httpx` throws `Invalid port: ':1]'`, the `no_proxy` env
contains `[::1]` which httpx misparses. Fix:
`export no_proxy='localhost,127.0.0.1,::1,198.19.0.1,198.19.0.2'`.

## 3. Entire (repo checkpoints)

Human does once in a browser: sign in at entire.io with GitHub, install the
Entire GitHub App on `warsang/vendorlens`, import the repo.

Then, in your clone:

```bash
curl -fsSL https://entire.io/install.sh | bash   # Linux; macOS: brew install --cask entireio/tap/entire
entire login --device                            # human approves the code in browser
entire enable --agent <your-agent>               # pick from: entire enable --help
# ... do work, then:
git commit -m "..."                              # answer "yes" to link session context
entire checkpoint list
entire checkpoint explain HEAD
```

The submission needs an accessible checkpoint **link + ID**. Put both in the
README and the X submission post.

## 4. cfo.ai (business plan)

Inputs live in `docs/business-plan-inputs.md`. Human pastes them into
cfo.ai (https://cfo.ai/neathacks, Google sign-in) and exports the plan.
The exported plan goes in the submission; keep a copy at
`docs/business-plan.md` if the human shares it with you.

## 5. Demo

- Interactive verdict demo: open `demo/index.html` in a real browser, hit
  **Assess** (needs `demo/vendor/` installed: `cd demo && npm install`).
- Demo video (≤3 min): follow `docs/demo-script.md`. It must explicitly
  cover neatlogs, Entire, and cfo.ai.

## 6. Build in public

Drafts in `docs/build-in-public.md`. **Never post without Theodore's
explicit approval of the exact text.** Posts go on X, tagged `#neatHack`.

## 7. Submission (Oct 12, 7:00–11:55 PM IST = 15:30–20:25 CEST)

Quote post of the official neatlogs X post with: team (`solohackaton`),
project name, public repo URL, demo link/video, Entire checkpoint link + ID,
cfo.ai business plan, neatlogs trace links. The repo MUST be public at
submission time. The exact quote-post text needs Theodore's explicit
approval before publishing.

## 8. Standing rules for this repo

- No secrets in code, ever. Env vars only, `.env` is gitignored.
- Public-facing copy is first person as a solo dev ("I"), not "we".
- No em dashes in prose. No stock AI phrases.
- Nothing publishes (posts, listings, submissions) without his explicit
  per-item approval. Announcing is not approval.
