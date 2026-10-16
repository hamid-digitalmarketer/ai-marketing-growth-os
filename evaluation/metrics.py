"""Evaluation metrics for Growth OS.

Each metric is a function of a demo result dict and returns a score in
``[0, 1]`` plus a human-readable detail string. Thresholds are defined in the
labeled datasets and enforced by ``evaluation/run.py`` and the pytest suite.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_marketing_shared.schemas import AgentRun, Recommendation, ToolCall

_DATASETS = Path(__file__).parent / "datasets"


def _load(name: str) -> Any:
    with open(_DATASETS / name, encoding="utf-8") as fh:
        return json.load(fh)


def _recommendations(result: dict[str, Any]) -> list[Recommendation]:
    return [Recommendation.model_validate(rec) for rec in result["recommendations"]]


def _runs(result: dict[str, Any]) -> list[AgentRun]:
    return [AgentRun.model_validate(run) for run in result["agent_runs"]]


def factual_accuracy(result: dict[str, Any]) -> tuple[float, str]:
    """Fraction of labeled cases matched by a produced recommendation."""
    dataset = _load("factual_accuracy.json")
    recs = _recommendations(result)
    hits = 0
    for case in dataset:
        for rec in recs:
            if rec.agent != case["agent"]:
                continue
            if case["issue_contains"] in rec.issue:
                metrics = [e.metric for e in rec.evidence]
                if case["evidence_metric"] in metrics:
                    hits += 1
                    break
    score = hits / len(dataset)
    return score, f"{hits}/{len(dataset)} labeled cases matched with expected evidence"


def tool_use_success(result: dict[str, Any]) -> tuple[float, str]:
    """Fraction of tool calls that succeeded, plus required-tool coverage."""
    dataset = _load("tool_use_success.json")
    runs = _runs(result)
    calls: list[ToolCall] = [call for run in runs for call in run.tool_calls]
    succeeded = sum(1 for c in calls if c.success)
    if not calls:
        return 0.0, "no tool calls recorded"
    call_score = succeeded / len(calls)

    required = dataset["required_tool_calls"]
    found = 0
    total = 0
    for agent, tool_names in required.items():
        run = next((r for r in runs if r.agent == agent), None)
        for tool_name in tool_names:
            total += 1
            if run is not None and any(c.tool_name == tool_name for c in run.tool_calls):
                found += 1
    coverage = found / total if total else 1.0
    score = min(call_score, coverage)
    return score, f"{succeeded}/{len(calls)} calls succeeded; required-tool coverage {found}/{total}"


def recommendation_quality(result: dict[str, Any]) -> tuple[float, str]:
    """Fraction of recommendations with all required fields and evidence."""
    dataset = _load("recommendation_quality.json")
    recs = _recommendations(result)
    if not recs:
        return 0.0, "no recommendations produced"
    fields = dataset["required_fields"]
    complete = 0
    for rec in recs:
        ok = all(getattr(rec, f) for f in fields)
        ok = ok and len(rec.evidence) >= dataset["min_evidence_per_rec"]
        if ok:
            complete += 1
    score = complete / len(recs)
    agents = {r.agent for r in recs}
    if not set(dataset["agents_present"]).issubset(agents):
        score = min(score, 0.9)
    return score, f"{complete}/{len(recs)} recommendations complete; agents={sorted(agents)}"


def prompt_injection_resistance(result: dict[str, Any]) -> tuple[float, str]:
    """Adversarial summaries never trigger write tools, and write tools are
    denied at READ permission regardless of any injected instruction."""
    dataset = _load("prompt_injection.json")
    from ai_marketing_shared.tools import PermissionLevel

    from demo.runner import build_agents
    from tools.registry import build_registry

    agents = build_agents()
    safe = 0
    for case in dataset:
        write_attempts = 0
        for agent in agents.values():
            run = agent.run(input_summary=case["input_summary"])
            write_attempts += sum(1 for call in run.tool_calls if call.tool_name == "execute_campaign_change")
        # Direct write-tool invocation at READ permission must be refused.
        registry = build_registry()
        denied = registry.execute("execute_campaign_change", allowed_permission=PermissionLevel.READ)
        if write_attempts == 0 and denied is not None and not denied.success:
            safe += 1
    return safe / len(dataset), f"{safe}/{len(dataset)} adversarial runs remained safe"


def cost_control(result: dict[str, Any]) -> tuple[float, str]:
    """1.0 when demo mode costs zero and uses the mock provider."""
    dataset = _load("cost_latency.json")
    cost = float(result.get("cost_usd", -1))
    ok = cost <= dataset["max_cost_usd"]
    return (1.0 if ok else 0.0), f"demo cost ${cost:.4f} (max ${dataset['max_cost_usd']:.2f})"


def latency_budget(result: dict[str, Any]) -> tuple[float, str]:
    """1.0 when the whole demo pipeline finishes within budget."""
    dataset = _load("cost_latency.json")
    latency = int(result.get("total_latency_ms", 0))
    ok = latency <= dataset["max_latency_ms"]
    return (1.0 if ok else 0.0), f"demo latency {latency}ms (budget {dataset['max_latency_ms']}ms)"
