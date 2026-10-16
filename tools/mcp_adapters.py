"""Concrete MCP adapter implementations.

Production integrations (Google Ads API, Meta Marketing API, GA4 Data API, a
real crawler) implement the shared :class:`McpAdapter` interface. These
concrete adapters are backed by the local sample data so demo mode exercises
the same code paths without credentials.
"""

from __future__ import annotations

from typing import Any

from ai_marketing_shared.mcp import McpAdapter

from data.connectors import load_table

_SERVERS: dict[str, tuple[str, list[str]]] = {
    "google_ads": ("google_ads_campaigns.csv", ["list_campaigns"]),
    "meta_ads": ("meta_ads_campaigns.csv", ["list_campaigns"]),
    "ga4": ("ga_sessions.csv", ["get_sessions"]),
    "gsc": ("gsc_keywords.csv", ["get_keyword_performance"]),
    "web_crawl": ("website_crawl.csv", ["get_pages"]),
}


class _LocalCsvAdapter(McpAdapter):
    """Base adapter serving sample CSV rows as MCP tool responses."""

    server_name = "local"

    def __init__(self) -> None:
        self._filename: str = ""
        self._tool_names: list[str] = []

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "description": f"{self.server_name} MCP tool backed by {self._filename}",
                "input_schema": {"type": "object", "properties": {}},
            }
            for name in self._tool_names
        ]

    def call_tool(self, *, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._tool_names:
            raise KeyError(f"Unknown {self.server_name} MCP tool: {name}")
        rows = load_table(self._filename)
        return {"rows": rows, "count": len(rows)}


class GoogleAdsMcpAdapter(_LocalCsvAdapter):
    server_name = "google_ads"

    def __init__(self) -> None:
        self._filename, self._tool_names = _SERVERS["google_ads"]


class MetaAdsMcpAdapter(_LocalCsvAdapter):
    server_name = "meta_ads"

    def __init__(self) -> None:
        self._filename, self._tool_names = _SERVERS["meta_ads"]


class Ga4McpAdapter(_LocalCsvAdapter):
    server_name = "ga4"

    def __init__(self) -> None:
        self._filename, self._tool_names = _SERVERS["ga4"]


class GscMcpAdapter(_LocalCsvAdapter):
    server_name = "gsc"

    def __init__(self) -> None:
        self._filename, self._tool_names = _SERVERS["gsc"]


class WebCrawlMcpAdapter(_LocalCsvAdapter):
    server_name = "web_crawl"

    def __init__(self) -> None:
        self._filename, self._tool_names = _SERVERS["web_crawl"]
