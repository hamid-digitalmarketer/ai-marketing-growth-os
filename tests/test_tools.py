"""Unit tests for the Growth OS tool layer."""

from __future__ import annotations

import pytest
from ai_marketing_shared.tools import PermissionLevel

from tools.registry import build_registry
from tools.write_tools import ExecuteCampaignChangeTool


@pytest.fixture()
def registry():
    return build_registry()


def test_registry_contains_all_read_tools(registry) -> None:
    names = {tool.name for tool in registry.list_tools()}
    assert names == {
        "fetch_website_crawl",
        "fetch_gsc_keywords",
        "fetch_pagespeed",
        "fetch_google_ads",
        "fetch_meta_ads",
        "fetch_ga_sessions",
        "fetch_product_catalog",
        "execute_campaign_change",
    }


def test_duplicate_registration_rejected(registry) -> None:
    with pytest.raises(ValueError):
        registry.register(ExecuteCampaignChangeTool())


@pytest.mark.parametrize(
    "tool_name, expected_columns",
    [
        ("fetch_website_crawl", ["url", "broken_links"]),
        ("fetch_gsc_keywords", ["query", "clicks", "impressions", "ctr", "position"]),
        ("fetch_pagespeed", ["url", "lcp_ms", "tbt_ms"]),
        ("fetch_google_ads", ["campaign", "cpa_usd", "roas"]),
        ("fetch_meta_ads", ["campaign", "cpa_usd", "roas"]),
        ("fetch_ga_sessions", ["sessions", "conversion_rate", "revenue_usd"]),
        ("fetch_product_catalog", ["sku", "inventory_level", "conversion_rate"]),
    ],
)
def test_read_tools_return_expected_data(registry, tool_name: str, expected_columns: list[str]) -> None:
    result = registry.execute(tool_name, allowed_permission=PermissionLevel.READ)
    assert result is not None and result.success
    rows = result.data["rows"]
    assert rows, f"{tool_name} returned no rows"
    for col in expected_columns:
        assert col in rows[0], f"{tool_name} row missing column {col}"


def test_read_tool_filter(registry) -> None:
    result = registry.execute(
        "fetch_gsc_keywords", allowed_permission=PermissionLevel.READ, filter_key="query", filter_value="buy sofa online"
    )
    assert result is not None and result.success
    assert all(r["query"] == "buy sofa online" for r in result.data["rows"])


def test_write_tool_denied_at_read_permission(registry) -> None:
    result = registry.execute(
        "execute_campaign_change",
        allowed_permission=PermissionLevel.READ,
        campaign="Brand Search",
        change="pause",
    )
    assert result is not None and not result.success
    assert "permission" in (result.error or "").lower()


def test_write_tool_records_dry_run(registry) -> None:
    result = registry.execute(
        "execute_campaign_change",
        allowed_permission=PermissionLevel.WRITE,
        campaign="Brand Search",
        change="pause",
    )
    assert result is not None and result.success
    assert result.data["applied"] is False


def test_unknown_tool_returns_none(registry) -> None:
    assert registry.execute("does_not_exist") is None
