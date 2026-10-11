#!/usr/bin/env python
"""Build the demo page.

Two supported builds:

  public (default)      no backend. Leaves the __AGENT_API__/__AGENT_TOKEN__
                        placeholders in place so AGENT_CONNECTED is false and
                        the page uses the "Load example" button (a committed
                        brief). This is what is committed and deployed to Pages.

  backend               substitutes a real gateway URL + public client token
                        from --api/--token (or AGENT_API/AGENT_TOKEN env) and
                        FAILS if any placeholder is left unreplaced.

Examples:
    python demo/build.py --public --out dist
    python demo/build.py --out dist --api https://...execute-api... --token TOK
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "index.html"
PLACEHOLDERS = ("__AGENT_API__", "__AGENT_TOKEN__")


def build(out: Path, api: str | None, token: str | None) -> int:
    html = SRC.read_text(encoding="utf-8")
    if api is not None:
        html = html.replace("__AGENT_API__", api)
    if token is not None:
        html = html.replace("__AGENT_TOKEN__", token)
    left = [p for p in PLACEHOLDERS if p in html]
    if api is not None or token is not None:
        # A backend build must not ship any unreplaced placeholder.
        if left:
            sys.stderr.write(
                f"error: placeholders left unreplaced: {left}\n"
                f"pass both --api and --token, or use --public for the "
                f"no-backend build.\n")
            return 2
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    # copy the vendored assets the page references
    import shutil
    for name in ("example.json", "jeveb", "vendor", ".nojekyll"):
        src = Path(__file__).resolve().parent / name
        if src.is_dir():
            shutil.copytree(src, out / name, dirs_exist_ok=True)
        elif src.exists():
            shutil.copy(src, out / name)
    kind = "public (no backend)" if api is None else "backend"
    print(f"built {kind} -> {out}  placeholders remaining: {left or 'none'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", action="store_true",
                    help="build the no-backend page (keeps placeholders)")
    ap.add_argument("--out", default="dist")
    ap.add_argument("--api", default=os.environ.get("AGENT_API"))
    ap.add_argument("--token", default=os.environ.get("AGENT_TOKEN"))
    a = ap.parse_args()
    if a.public:
        return build(Path(a.out), None, None)
    return build(Path(a.out), a.api, a.token)


if __name__ == "__main__":
    raise SystemExit(main())
