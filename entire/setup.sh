#!/usr/bin/env bash
# Entire setup for the VendorLens repo (run by a human; GitHub auth is manual).
# Docs: https://hack.entire.io/neathacks-2026/
set -euo pipefail

echo "== 1. Install the Entire CLI =="
if command -v entire >/dev/null 2>&1; then
  echo "entire already installed: $(entire --version 2>/dev/null || true)"
elif command -v brew >/dev/null 2>&1; then
  brew install --cask entireio/tap/entire
else
  echo "No brew found. Install per https://docs.entire.io quickstart,"
  echo "then re-run this script."
  exit 1
fi

echo "== 2. Enable Entire in this repo =="
cd "$(dirname "$0")/.."
# 'generic' integration captures sessions for agents Entire doesn't know natively.
entire enable --agent generic || entire enable

echo "== 3. Verify =="
entire status || true

echo
echo "Next (manual, in browser):"
echo "  1. Sign in at https://entire.io with 'Sign in with GitHub'."
echo "  2. As GitHub org admin, install the Entire GitHub App and import"
echo "     the warsang/vendorlens repository."
echo "  3. Commit code; answer 'yes' when prompted to link session context."
echo "  4. entire checkpoint list && entire checkpoint explain HEAD"
echo "  5. Paste the checkpoint link + ID into the submission."
