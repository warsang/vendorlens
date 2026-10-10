"""Tool registry. Each tool exposes: name, description, and async run(args, ctx)."""
from __future__ import annotations

from . import crustdata, dns_tool, homepage, tls_tool, websearch, whois_tool

TOOLS = {
    crustdata.NAME: crustdata,
    dns_tool.NAME: dns_tool,
    whois_tool.NAME: whois_tool,
    tls_tool.NAME: tls_tool,
    homepage.NAME: homepage,
    websearch.NAME: websearch,
}

__all__ = ["TOOLS"]
