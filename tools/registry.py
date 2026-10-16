"""Central tool registry for Growth OS.

Agents never instantiate tools directly; they resolve them through this
registry so permission gating and audit hooks apply uniformly.
"""

from __future__ import annotations

from ai_marketing_shared.tools import ToolRegistry

from tools.data_tools import (
    FetchGaSessionsTool,
    FetchGoogleAdsTool,
    FetchGscKeywordsTool,
    FetchMetaAdsTool,
    FetchPagespeedTool,
    FetchProductCatalogTool,
    FetchWebsiteCrawlTool,
)
from tools.write_tools import ExecuteCampaignChangeTool


def build_registry() -> ToolRegistry:
    """Build and populate the Growth OS tool registry."""
    registry = ToolRegistry()
    for tool in (
        FetchWebsiteCrawlTool(),
        FetchGscKeywordsTool(),
        FetchPagespeedTool(),
        FetchGoogleAdsTool(),
        FetchMetaAdsTool(),
        FetchGaSessionsTool(),
        FetchProductCatalogTool(),
        ExecuteCampaignChangeTool(),
    ):
        registry.register(tool)
    return registry
