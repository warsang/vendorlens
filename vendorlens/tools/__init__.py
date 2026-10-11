"""Tool registry. Each tool exposes: name, description, and async run(args, ctx)."""
from __future__ import annotations

from . import (crustdata, ct_logs, dns_tool, doh_dns, homepage, phishtank_check,
               rdap_lookup, tls_tool, urlscan_reputation, websearch, whois_tool)

TOOLS = {
    crustdata.NAME: crustdata,
    dns_tool.NAME: dns_tool,
    doh_dns.NAME: doh_dns,
    whois_tool.NAME: whois_tool,
    rdap_lookup.NAME: rdap_lookup,
    ct_logs.NAME: ct_logs,
    tls_tool.NAME: tls_tool,
    homepage.NAME: homepage,
    websearch.NAME: websearch,
    urlscan_reputation.NAME: urlscan_reputation,
    phishtank_check.NAME: phishtank_check,
}

__all__ = ["TOOLS"]
