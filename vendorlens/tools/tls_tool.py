"""TLS certificate inspection: expiry date and issuer."""
from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone

NAME = "tls_inspect"
DESCRIPTION = ("Fetch the TLS certificate: expiry date, issuer, days left. "
               "Expiring/self-signed certs are operational risk signals.")


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
        not_after = datetime.strptime(
            cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc)
        issuer = dict(x[0] for x in cert.get("issuer", ()))
        subject = dict(x[0] for x in cert.get("subject", ()))
        days_left = (not_after - datetime.now(timezone.utc)).days
        return {"ok": True, "data": {
            "issuer": issuer.get("organizationName"),
            "subject_cn": subject.get("commonName"),
            "not_after": not_after.isoformat(),
            "days_left": days_left,
            "self_signed": issuer.get("organizationName") == subject.get(
                "organizationName"),
        }, "sources": [f"tls:{domain}:443"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
