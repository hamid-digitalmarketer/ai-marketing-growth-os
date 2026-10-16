"""Unit tests for the Growth OS agents."""

from __future__ import annotations

import pytest
from ai_marketing_shared.schemas import AgentStatus, ApprovalStatus

from agents import AdsAgent, AnalyticsAgent, EcommerceAgent, SeoAgent
from tools.registry import build_registry


@pytest.fixture()
def registry():
    return build_registry()


@pytest.mark.parametrize(
    "agent_cls",
    [SeoAgent, AdsAgent, EcommerceAgent, AnalyticsAgent],
)
def test_every_agent_produces_traced_run(agent_cls, registry) -> None:
    agent = agent_cls(registry)
    run = agent.run(input_summary="unit test")
    assert run.status == AgentStatus.COMPLETED
    assert run.error is None
    assert run.tool_calls, f"{agent_cls.name} made no tool calls"
    assert all(call.success for call in run.tool_calls)
    assert run.api_cost_estimate == 0.0
    assert run.latency_ms >= 0
    assert run.recommendations, f"{agent_cls.name} produced no recommendations"


def test_seo_agent_detects_known_issues(registry) -> None:
    run = SeoAgent(registry).run()
    issues = [r.issue for r in run.recommendations]
    assert any("Broken links" in i for i in issues)
    assert any("Missing meta description" in i for i in issues)
    assert any("Low CTR" in i for i in issues)
    assert any("Slow LCP" in i for i in issues)


def test_ads_agent_detects_cpa_and_roas_issues(registry) -> None:
    run = AdsAgent(registry).run()
    issues = [r.issue for r in run.recommendations]
    assert any("High CPA" in i for i in issues)
    assert any("Low ROAS" in i for i in issues)


def test_ecommerce_agent_detects_stock_issues(registry) -> None:
    run = EcommerceAgent(registry).run()
    issues = [r.issue for r in run.recommendations]
    assert any("Stock-out" in i for i in issues)
    assert any("Low inventory" in i for i in issues)


def test_analytics_agent_detects_conversion_decline(registry) -> None:
    run = AnalyticsAgent(registry).run()
    issues = [r.issue for r in run.recommendations]
    assert any("Conversion rate declining" in i for i in issues)


def test_all_recommendations_are_evidence_backed(registry) -> None:
    for agent_cls in (SeoAgent, AdsAgent, EcommerceAgent, AnalyticsAgent):
        run = agent_cls(registry).run()
        for rec in run.recommendations:
            assert rec.evidence, f"{agent_cls.name} produced evidence-less recommendation"
            assert rec.proposed_action
            assert rec.requires_approval is True
            assert rec.status == ApprovalStatus.PENDING


def test_agents_never_call_write_tools(registry) -> None:
    for agent_cls in (SeoAgent, AdsAgent, EcommerceAgent, AnalyticsAgent):
        run = agent_cls(registry).run()
        assert all(call.tool_name != "execute_campaign_change" for call in run.tool_calls)
