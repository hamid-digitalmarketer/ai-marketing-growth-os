"""Unit tests for the rule-based demo mode."""

from __future__ import annotations

import pytest

from demo.runner import run_demo


def test_demo_runs_all_agents() -> None:
    result = run_demo()
    assert result["mode"] == "rule-based"
    assert result["provider"] == "mock"
    assert result["cost_usd"] == 0.0
    assert {run["agent"] for run in result["agent_runs"]} == {"seo", "ads", "ecommerce", "analytics"}
    assert len(result["recommendations"]) >= 8
    assert result["approval_queue"], "approval queue must be populated"
    assert result["tool_calls"] > 0


def test_demo_subset_of_agents() -> None:
    result = run_demo(agents=["seo"])
    assert len(result["agent_runs"]) == 1
    assert result["agent_runs"][0]["agent"] == "seo"


def test_demo_unknown_agent_raises() -> None:
    with pytest.raises(KeyError):
        run_demo(agents=["nope"])


def test_demo_recommendations_are_json_serializable() -> None:
    import json

    result = run_demo()
    json.dumps(result)  # must not raise


def test_demo_approval_items_are_pending() -> None:
    result = run_demo()
    assert all(item["status"] == "pending" for item in result["approval_queue"])
