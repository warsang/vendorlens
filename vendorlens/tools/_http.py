"""Shared HTTP helpers: a retrying GET for the external OSINT sources.

These endpoints (crt.sh, PhishTank, urlscan) occasionally reset a large
transfer. A single immediate retry removes most of the flakiness without
hiding genuine failures, which the agent still records and works around.
"""
from __future__ import annotations

import asyncio
import re

_TRANSIENT_HINTS = (
    "timed out", "timeout", "reset", "refused", "connection error",
    "connectionerror", "incompleteread", "broken pipe",
    "temporarily unavailable", "overloaded", "too many requests",
    "bad gateway", "service unavailable", "gateway time",
)
_NON_TRANSIENT_HINTS = (
    "not found", "no records", "did not resolve", "invalid domain",
    "refusing to fetch", "redirect to invalid", "redirect to non-public",
    "unprocessable", "no company", "too large", "forbidden",
)
_STATUS_RE = re.compile(r"\b(4\d\d|5\d\d)\b")


def is_transient_error(msg) -> bool:
    """Decide whether a tool error is worth retrying.

    Only transient conditions (timeouts, connection resets, 429, 5xx) are
    retried. Deterministic failures (404, NXDOMAIN, invalid domain, "not
    found") are not, so a bad vendor never wastes ~14s sleeping on a result
    that cannot change (P1.3).
    """
    m = (str(msg) if msg is not None else "").lower()
    status = _STATUS_RE.search(m)
    if status:
        code = int(status.group(1))
        if code == 429 or code >= 500:
            return True
        if 400 <= code < 500:
            return False
    return any(h in m for h in _TRANSIENT_HINTS) and \
        not any(h in m for h in _NON_TRANSIENT_HINTS)



async def get_with_retry(client, url: str, *, attempts: int = 3, timeout=None,
                         **kwargs):
    """GET `url`, retrying transient network errors with a short backoff."""
    last: Exception | None = None
    for i in range(attempts):
        try:
            return await client.get(url, timeout=timeout, **kwargs)
        except Exception as exc:  # noqa: BLE001
            last = exc
            if i < attempts - 1:
                await asyncio.sleep(1.5 * (i + 1))
    raise last if last else RuntimeError("request failed")


async def post_with_retry(client, url: str, *, attempts: int = 2, timeout=None,
                          **kwargs):
    """POST `url`, retrying transient network errors with a short backoff."""
    last: Exception | None = None
    for i in range(attempts):
        try:
            return await client.post(url, timeout=timeout, **kwargs)
        except Exception as exc:  # noqa: BLE001
            last = exc
            if i < attempts - 1:
                await asyncio.sleep(1.5 * (i + 1))
    raise last if last else RuntimeError("request failed")
