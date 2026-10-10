# Entire evidence for VendorLens (neatHack 2026)

Entire is the "git forge for AI-native teams": the CLI captures the coding
agent sessions behind each commit, and Checkpoints tie a Git commit to the
decisions that produced it.

## What we use it for

- **Checkpoints**: every commit links to the agent session context behind it
  (`entire checkpoint list`, `entire checkpoint explain HEAD`).
- **Entire Graph** (optional stretch): `entire plugin install graph` to map
  repo relationships; useful in the demo to show where the risk-scoring
  weights live and what touches them.

## Setup (human steps; coding agents can't do the browser parts)

1. Run `./entire/setup.sh` (installs CLI, runs `entire enable`).
2. Sign in at https://entire.io with **Sign in with GitHub**.
3. As the GitHub org/user admin, install the Entire GitHub App and import
   `warsang/vendorlens`.
4. Work normally; when committing, answer **yes** to link session context.
5. Inspect: `entire checkpoint list`, `entire checkpoint explain HEAD`.
6. For the submission: include an accessible checkpoint link + checkpoint ID.

## Submission checklist mapping

- "You used Entire" -> checkpoint link + ID in the repo README and the
  X submission post.
- "Checkpoints or entire-graph output" -> screenshot of
  `entire checkpoint explain HEAD` in the demo video (20% of the score
  is the demo; the video must explicitly cover Entire).
