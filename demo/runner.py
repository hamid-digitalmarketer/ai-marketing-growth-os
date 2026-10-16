"""Growth OS rule-based demo mode.

Runs the full agent pipeline on sample data with the mock provider: zero API
keys, zero cost, fully observable traces. This is the default mode for
``docker compose up``, CI, and anyone cloning the repo.
"""

from __future__ import annotations

from typing import Any

from ai_marketing_shared.providers import ProviderFactory

from agents import AdsAgent, AnalyticsAgent, EcommerceAgent, SeoAgent
from agents.base import BaseAgent
from orchestration.approval import ApprovalQueue
from orchestration.planner import build_plan
from tools.registry import build_registry

_ALL_AGENTS: tuple[type[BaseAgent], ...] = (SeoAgent, AdsAgent, EcommerceAgent, AnalyticsAgent)


def build_agents() -> dict[str, BaseAgent]:
    registry = build_registry()
    return {cls.name: cls(registry) for cls in _ALL_AGENTS}


def run_demo(*, agents: list[str] | None = None) -> dict[str, Any]:
    """Run the demo pipeline and return dashboard-ready JSON."""
    provider = ProviderFactory.get_provider()
    provider_name = provider.provider_name
    agent_map = build_agents()
    names = agents or list(agent_map.keys())
    unknown = [n for n in names if n not in agent_map]
    if unknown:
        raise KeyError(f"Unknown agents: {unknown}")

    runs = [agent_map[name].run(input_summary="demo-mode full pipeline") for name in names]
    recommendations = [rec for run in runs for rec in run.recommendations]
    plan = build_plan(recommendations)
    queue = ApprovalQueue()
    items = queue.enqueue_many(plan.recommendations)

    return {
        "provider": provider_name,
        "mode": "rule-based",
        "cost_usd": 0.0,
        "agent_runs": [run.model_dump(mode="json") for run in runs],
        "recommendations": [rec.model_dump(mode="json") for rec in plan.recommendations],
        "plan": plan.to_dict(),
        "approval_queue": [item.model_dump(mode="json") for item in items],
        "total_latency_ms": sum(run.latency_ms for run in runs),
        "tool_calls": sum(len(run.tool_calls) for run in runs),
    }
