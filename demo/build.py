#!/usr/bin/env python
"""Build the demo page.

The page is live-only: it always invokes the deployed agent gateway
(`__AGENT_API__` + public client token `__AGENT_TOKEN__`). This build
substitutes both values into demo/index.html and FAILS if either is missing
or any placeholder is left unreplaced.

Values come from (in order): --api/--token, the AGENT_API/AGENT_TOKEN env
vars, or the gitignored deploy/.deploy.local (ENDPOINT= / PUBLIC_TOKEN=).

Example:
    python demo/build.py --out dist
    wrangler pages deploy dist --project-name vendorlens-demo
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "index.html"
PLACEHOLDERS = ("__AGENT_API__", "__AGENT_TOKEN__")
DEPLOY_LOCAL = HERE.parent / "deploy" / ".deploy.local"


def from_deploy_local() -> dict:
    values: dict[str, str] = {}
    if DEPLOY_LOCAL.exists():
        for line in DEPLOY_LOCAL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    return values


def build(out: Path, api: str | None, token: str | None) -> int:
    missing = [flag for flag, value in (("--api/AGENT_API", api),
                                        ("--token/AGENT_TOKEN", token))
               if not value]
    if missing:
        sys.stderr.write(
            "error: the demo page is live-only; missing " + ", ".join(missing) + ".\n"
            "Pass both --api and --token, set AGENT_API/AGENT_TOKEN, or fill the\n"
            f"gitignored {DEPLOY_LOCAL} (ENDPOINT=, PUBLIC_TOKEN=).\n")
        return 2
    html = SRC.read_text(encoding="utf-8")
    html = html.replace("__AGENT_API__", api).replace("__AGENT_TOKEN__", token)
    left = [p for p in PLACEHOLDERS if p in html]
    if left:  # defensive: the source must not ship a placeholder in a live build
        sys.stderr.write(f"error: placeholders left unreplaced: {left}\n")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    # copy the vendored assets the page references
    for name in ("jeveb", "vendor", ".nojekyll"):
        src = HERE / name
        if src.is_dir():
            shutil.copytree(src, out / name, dirs_exist_ok=True)
        elif src.exists():
            shutil.copy(src, out / name)
    print(f"built live demo -> {out}  (agent endpoint + client token substituted)")
    return 0


def main() -> int:
    local = from_deploy_local()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    ap.add_argument("--api", default=os.environ.get("AGENT_API") or local.get("ENDPOINT"))
    ap.add_argument("--token", default=os.environ.get("AGENT_TOKEN") or local.get("PUBLIC_TOKEN"))
    a = ap.parse_args()
    return build(Path(a.out), a.api, a.token)


if __name__ == "__main__":
    raise SystemExit(main())
