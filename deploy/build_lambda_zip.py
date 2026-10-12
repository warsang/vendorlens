#!/usr/bin/env python
"""Build the AWS Lambda deployment zip for the VendorLens handler.

    python deploy/build_lambda_zip.py            # -> deploy/vendorlens-lambda.zip

Installs only the packages the handler actually imports at runtime (httpx,
openai, dnspython, trafilatura) plus the `vendorlens` package, and writes a
zip ready for `aws lambda update-function-code`. neatlogs stays an optional
import (tracing degrades to a no-op without it).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "deploy" / "_build"
ZIP = ROOT / "deploy" / "vendorlens-lambda.zip"
DEPS = ["httpx", "openai", "dnspython", "trafilatura"]


def main() -> int:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    print("installing runtime deps into the build dir...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "--target", str(BUILD), *DEPS], check=True)
    print("copying the vendorlens package...")
    shutil.copytree(ROOT / "vendorlens", BUILD / "vendorlens",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # the handler entry point is vendorlens.aws_lambda.lambda_handler
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in BUILD.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(BUILD))
    size = ZIP.stat().st_size / 1e6
    print(f"wrote {ZIP.relative_to(ROOT)}  ({size:.1f} MB)")
    if size > 50:
        print("WARNING: over the 50 MB zipped direct-upload limit; "
              "use an S3 upload.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
