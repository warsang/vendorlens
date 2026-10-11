# Demo video script — VendorLens (produced, 1:44)

The video is committed at `docs/demo.mp4` (release asset:
https://github.com/warsang/vendorlens/releases/tag/demo). It explicitly covers
all three mandatory tools: neatlogs, Entire and cfo.ai. The slide source is
`docs/video-slides.html` (nine scenes, dark terminal aesthetic, SAPI narration).

## Scene timings (produced video)

| Time | Scene | Content |
|---|---|---|
| 0:00-0:04 | 1 Title | VendorLens, know your vendor before you wire; neatHack 2026 |
| 0:04-0:17 | 2 Problem | "Is this counterparty a real business, or a front?" URL checkers cannot answer it |
| 0:17-0:40 | 3 Agent live | `python -m vendorlens acme-cloud-services.example --demo`: planner picks 9 tools, MEDIUM 48/100 verdict, cited signals |
| 0:40-0:52 | 4 Failure and recovery | real trace.jsonl from the amazon.com run: phishtank_check 503, retry with backoff, run continues |
| 0:52-1:06 | 5 neatlogs | init + wrapped OpenAI client, one WORKFLOW span per run, dashboard + committed trace evidence |
| 1:06-1:14 | 6 Entire | checkpoint list / explain, checkpoint link in the submission |
| 1:14-1:25 | 7 cfo.ai | pricing tiers, unit economics, revenue scenarios, costs and runway |
| 1:25-1:40 | 8 On-device verdict | Bekko 17m typed-decision bars from the public demo page; zero network after weights load |
| 1:40-1:44 | 9 Close | repo + pages.dev demo links |

## B-roll used (all committed)

- `runs/acme-cloud-services.example/20261011T215709Z` (canned run replayed by
  the public demo page)
- `runs/amazon.com/20261011T203036Z/trace.jsonl` (real retry/backoff events)
- `runs/linear.app/20261011T215820Z/brief.md` (live LLM-planned run)
- Entire checkpoint link (scene 6)

## Narration style

Microsoft David (SAPI), rate 0, one paragraph per scene, matching the
narration lines in `docs/video-slides.html`.
