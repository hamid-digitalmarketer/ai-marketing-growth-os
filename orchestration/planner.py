"""Unified action planning: deduplicate, prioritize, and summarize.

The orchestrator collects recommendations from every agent, removes duplicates
(normalized agent + issue), sorts by priority, and produces a single unified
action plan for the dashboard and approval queue.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ai_marketing_shared.schemas import Confidence, Priority, Recommendation

_PRIORITY_RANK = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}
_CONFIDENCE_RANK = {
    Confidence.HIGH: 0,
    Confidence.MEDIUM: 1,
    Confidence.LOW: 2,
}


@dataclass
class UnifiedPlan:
    """A deduplicated, prioritized action plan across all agents."""

    recommendations: list[Recommendation] = field(default_factory=list)
    created_summary: str = ""

    def stats(self) -> dict[str, Any]:
        by_agent: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        for rec in self.recommendations:
            by_agent[rec.agent] = by_agent.get(rec.agent, 0) + 1
            by_priority[rec.priority.value] = by_priority.get(rec.priority.value, 0) + 1
        return {
            "total": len(self.recommendations),
            "by_agent": by_agent,
            "by_priority": by_priority,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "stats": self.stats(),
            "recommendations": [rec.model_dump(mode="json") for rec in self.recommendations],
        }


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def deduplicate(recommendations: list[Recommendation]) -> list[Recommendation]:
    """Drop later recommendations with the same (agent, normalized issue)."""
    seen: set[tuple[str, str]] = set()
    result: list[Recommendation] = []
    for rec in recommendations:
        key = (rec.agent, _normalize(rec.issue))
        if key in seen:
            continue
        seen.add(key)
        result.append(rec)
    return result


def prioritize(recommendations: list[Recommendation]) -> list[Recommendation]:
    """Sort by priority (critical first), then by confidence."""
    return sorted(
        recommendations,
        key=lambda r: (_PRIORITY_RANK.get(r.priority, 9), _CONFIDENCE_RANK.get(r.confidence, 9)),
    )


def build_plan(recommendations: list[Recommendation]) -> UnifiedPlan:
    """Build the unified action plan from raw agent recommendations."""
    unique = deduplicate(recommendations)
    ordered = prioritize(unique)
    plan = UnifiedPlan(recommendations=ordered)
    plan.created_summary = (
        f"Plan contains {len(ordered)} unique recommendations "
        f"across {len({r.agent for r in ordered})} agents"
    )
    return plan
