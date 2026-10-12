# Demo video script -- VendorLens (<= 3 minutes)

Target 2:45. The video MUST explicitly cover neatlogs, Entire and cfo.ai
(they are a mandatory tool set). Recommended story per the judging brief: one
legitimate vendor (LOW) and one suspicious domain (CRITICAL) side by side,
one injected failure recovering, the brief with correct clickable citations and
the confidence column, the neatlogs trace with nested tool spans, the Entire
checkpoint, and the cfo.ai plan.

## Status

- The committed `docs/demo.mp4` (2:41) is built from `docs/video-slides.html`
  with `python docs/build_video.py` (headless scene screenshots + Windows SAPI
  narration + ffmpeg) and reflects the current behaviour: CRITICAL 100/100 for
  the canned suspicious run, classified retry/recovery, the confidence column,
  and the corrected business-plan numbers.
- The GitHub release asset at `releases/tag/demo` should be refreshed with the
  current mp4 (re-upload is a GitHub UI step).
- Re-record or rebuild any time; keep it under 3 minutes.

## Final script

| Time | Scene | Content |
|---|---|---|
| 0:00-0:20 | Problem | "Is this counterparty a real business, or a front?" A URL checker cannot tell you whether the company behind it exists |
| 0:20-1:05 | Agent, suspicious | `python -m vendorlens acme-cloud-services.example --demo`: 9 tools, verdict CRITICAL 100/100, every signal cited; a young domain triggers the rule-based phishing-feed check |
| 1:05-1:30 | Recovery | `python -m vendorlens acme-cloud-services.example --demo --inject-failure ct_logs:2`: `tool_retry` x2 then `tool_recovered` visible in `trace.jsonl` |
| 1:30-1:55 | neatlogs | one WORKFLOW span with nested TOOL spans; `neatlogs live tracing: on` in committed live runs |
| 1:55-2:15 | Entire | `entire checkpoint explain HEAD`; checkpoint link + ID in the submission |
| 2:15-2:35 | cfo.ai | pricing tiers, unit economics, runway and breakeven (see `docs/business-plan-inputs.md`) |
| 2:35-2:45 | On-device verdict + close | public demo page "Load example" -> Bekko 17m bars, zero network after weights load; repo + pages.dev links |

## Evidence to have on screen

- `examples/stripe.com/brief.md` (LOW, live) vs `examples/suspicious-acme.example/brief.md` (CRITICAL).
- `examples/injected-failure-acme.example/trace.jsonl` (failure -> retry -> recovery).
- The brief's **Confidence** column and **What we could not verify** section.
- Entire checkpoint link + ID; cfo.ai plan; neatlogs trace links (baseline and improved).
