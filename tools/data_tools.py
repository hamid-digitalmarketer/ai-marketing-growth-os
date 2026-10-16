"""Read-only tools backed by local sample data.

Every tool extends the shared :class:`BaseTool` and stays at READ permission so
demo mode (and any context without explicit write authorization) can never
mutate external systems. Data comes from precomputed CSVs; agents never
invent numbers.
"""

from __future__ import annotations

from typing import Any

from ai_marketing_shared.tools import BaseTool, PermissionLevel, ToolResult

from data.connectors import load_table


class _CsvReadTool(BaseTool):
    """Base for CSV-backed read tools."""

    filename: str = ""
    permission = PermissionLevel.READ

    def _rows(self, **arguments: Any) -> list[dict[str, Any]]:
        rows = load_table(self.filename)
        filter_key = arguments.get("filter_key")
        filter_value = arguments.get("filter_value")
        if filter_key and filter_value:
            rows = [r for r in rows if str(r.get(filter_key)) == str(filter_value)]
        return rows

    def _run(self, **arguments: Any) -> ToolResult:
        rows = self._rows(**arguments)
        if not rows:
            return ToolResult(success=False, error=f"No rows found in {self.filename}", data={"rows": []})
        summary = f"{len(rows)} rows from {self.filename}"
        return ToolResult(summary=summary, data={"rows": rows, "count": len(rows)})


class FetchWebsiteCrawlTool(_CsvReadTool):
    name = "fetch_website_crawl"
    description = "Fetch crawled site pages with meta description, broken links, and load speed."
    filename = "website_crawl.csv"


class FetchGscKeywordsTool(_CsvReadTool):
    name = "fetch_gsc_keywords"
    description = "Fetch Google Search Console keyword rows (clicks, impressions, CTR, position)."
    filename = "gsc_keywords.csv"


class FetchPagespeedTool(_CsvReadTool):
    name = "fetch_pagespeed"
    description = "Fetch Lighthouse-style PageSpeed metrics per URL."
    filename = "pagespeed_metrics.csv"


class FetchGoogleAdsTool(_CsvReadTool):
    name = "fetch_google_ads"
    description = "Fetch Google Ads campaign performance (spend, CPA, CTR, ROAS)."
    filename = "google_ads_campaigns.csv"


class FetchMetaAdsTool(_CsvReadTool):
    name = "fetch_meta_ads"
    description = "Fetch Meta Ads campaign performance (spend, CPA, CTR, ROAS)."
    filename = "meta_ads_campaigns.csv"


class FetchGaSessionsTool(_CsvReadTool):
    name = "fetch_ga_sessions"
    description = "Fetch GA-style session/revenue series, optionally filtered by device."
    filename = "ga_sessions.csv"


class FetchProductCatalogTool(_CsvReadTool):
    name = "fetch_product_catalog"
    description = "Fetch product catalog rows (inventory, price, conversion rate)."
    filename = "product_catalog.csv"
