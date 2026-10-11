"""VendorLens: AI agent for vendor due-diligence OSINT."""
from __future__ import annotations

__version__ = "0.1.0"

# Load .env (gitignored) into os.environ on package import, so keys placed
# there are picked up without exporting them. Real exported env vars take
# precedence. A missing .env or missing python-dotenv is a silent no-op, so
# --demo and --no-llm keep working with zero keys.
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass
