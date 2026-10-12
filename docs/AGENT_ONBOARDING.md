# VendorLens setup and release checklist

This doc is the maintainer-facing companion to the README: get from a clean
clone to a fully-wired local run, then the release checklist for the hackathon.

## 1. Environment

```bash
./setup.sh          # interactive: writes a chmod-600 .env (gitignored, never committed)
```

Optional keys (all in `.env`, never in code):

| Var | Where to get it |
|---|---|
| `NEATLOGS_API_KEY` | app.neatlogs.com -> project -> Settings -> API keys (the Project key, not the `nlw_` ingest key) |
| `CRUSTDATA_API_KEY` | app.crustdata.com -> dashboard -> API key |
| `LITELLM_API_BASE` / `LITELLM_API_KEY` / `LITELLM_MODEL` | the hackathon shared gateway (optional) |
| local LLM alt | `LITELLM_API_BASE=http://localhost:11434/v1` (Ollama), any model name |

No LLM key? Use `--no-llm` (live tools, deterministic plan). `--demo` runs
everything on canned data with zero keys.

## 2. Run it

```bash
python -m vendorlens <domain> --no-llm     # no LLM key needed
python -m vendorlens <domain>              # full LLM planning (needs LITELLM_*)
python -m vendorlens <domain> --demo       # canned, no keys
python -m vendorlens.eval                  # offline score check over examples/
pytest                                     # tests
```

Artifacts: `runs/<domain>/<ts>/` -> `brief.md`, `state.json`, `trace.jsonl`.
neatlogs tracing is automatic when `NEATLOGS_API_KEY` is set.

Sandbox note: if `httpx` throws `Invalid port: ':1]'`, the `no_proxy` env
contains `[::1]` which httpx misparses. Fix:
`export no_proxy='localhost,127.0.0.1,::1,198.19.0.1,198.19.0.2'`.

## 3. Entire (repo checkpoints)

Sign in at entire.io with GitHub, install the Entire GitHub App on
`warsang/vendorlens`, import the repo, then in your clone:

```bash
entire login --device
entire enable --agent opencode
git commit -m "..."          # answer "yes" to link the session
entire checkpoint list
entire checkpoint explain HEAD
```

The submission needs the checkpoint **link + ID**.

## 4. cfo.ai (business plan)

Paste `docs/business-plan-inputs.md` into cfo.ai (https://cfo.ai/neathacks)
and export the plan. Follow cfo.ai's own billing instructions; do not leave a
card on a paid plan.

## 5. Demo page

The page is live-only: the build substitutes the deployed gateway URL and the
public client token (from `--api`/`--token`, the env, or the gitignored
`deploy/.deploy.local`) and fails if either is missing.

```bash
python demo/build.py --out dist         # reads deploy/.deploy.local
python -m http.server -d dist 8000      # localhost is not the pinned origin
wrangler pages deploy dist --project-name vendorlens-demo
```

## 6. Release checklist

- [ ] `pytest` green; `python -m vendorlens.eval` matches expectations.
- [ ] `examples/` regenerated with `python examples/_regen.py`.
- [ ] neatlogs runs show a WORKFLOW span with nested TOOL spans.
- [ ] Entire checkpoint captured for the release commit (link + ID saved).
- [ ] cfo.ai plan exported and linked; no card left on a paid plan.
- [ ] Lambda: ALLOWED_ORIGIN pinned (not `*`), per-IP rate limit + daily budget
      alarm set, reserved concurrency configured, domain strict-validated.
- [ ] Demo page built from a clean clone (`python demo/build.py --out dist`)
      and deployed live (a real domain returns a fresh verdict at
      https://vendorlens-demo.pages.dev).
- [ ] Record <=3 min video (docs/demo-script.md), show neatlogs + Entire + cfo.ai.
- [ ] Repo public; commits within Oct 10-12; no secrets in history.
- [ ] Submit in the Oct 12 7:00-11:55 PM IST window, quote-posting neatlogs.
