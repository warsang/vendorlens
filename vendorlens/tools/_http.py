"""Shared HTTP helpers: a retrying GET for the external OSINT sources.

These endpoints (crt.sh, PhishTank, urlscan) occasionally reset a large
transfer. A single immediate retry removes most of the flakiness without
hiding genuine failures, which the agent still records and works around.
"""
from __future__ import annotations

import asyncio


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
