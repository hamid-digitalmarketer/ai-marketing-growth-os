"""Unit tests for orchestration: approval queue and unified planning."""

from __future__ import annotations

import pytest
from ai_marketing_shared.schemas import (
    ApprovalStatus,
    Confidence,
    Effort,
    Evidence,
    Priority,
    Recommendation,
)

from orchestration.approval import ApprovalQueue
from orchestration.planner import build_plan, deduplicate, prioritize


def _rec(agent: str, issue: str, priority: Priority = Priority.MEDIUM) -> Recommendation:
    return Recommendation(
        agent=agent,
        issue=issue,
        evidence=[Evidence(source="test", metric="x", value=1.0)],
        priority=priority,
        confidence=Confidence.HIGH,
        proposed_action="do something",
        expected_impact="+1%",
        effort=Effort.LOW,
        next_steps=["step 1"],
        requires_approval=True,
    )


def test_approval_queue_full_state_machine() -> None:
    queue = ApprovalQueue()
    item = queue.enqueue(_rec("seo", "Broken links"))
    assert item.status == ApprovalStatus.PENDING
    assert queue.stats()["pending"] == 1

    decided = queue.decide(item.id, approve=True, approver="ops-lead")
    assert decided.status == ApprovalStatus.APPROVED
    assert decided.approver == "ops-lead"
    assert decided.decided_at is not None

    executed = queue.execute(item.id, approver="ops-lead")
    assert executed.status == ApprovalStatus.EXECUTED

    measured = queue.measure(item.id, outcome="clicks +8%")
    assert measured.status == ApprovalStatus.MEASURED
    assert measured.outcome == "clicks +8%"


def test_approval_queue_rejects_illegal_transitions() -> None:
    queue = ApprovalQueue()
    item = queue.enqueue(_rec("seo", "Meta missing"))
    with pytest.raises(ValueError):
        queue.execute(item.id, approver="ops-lead")  # pending -> executed not allowed
    with pytest.raises(ValueError):
        queue.measure(item.id, outcome="x")  # pending -> measured not allowed

    queue.decide(item.id, approve=False, approver="ops-lead")
    with pytest.raises(ValueError):
        queue.decide(item.id, approve=True, approver="ops-lead")  # rejected is terminal


def test_approval_queue_unknown_item_raises() -> None:
    queue = ApprovalQueue()
    with pytest.raises(KeyError):
        queue.decide("missing", approve=True, approver="ops-lead")


def test_deduplicate_removes_same_issue() -> None:
    recs = [_rec("seo", "Broken links on /x"), _rec("seo", "Broken links on /x"), _rec("seo", "Slow LCP")]
    unique = deduplicate(recs)
    assert len(unique) == 2


def test_prioritize_sorts_critical_first() -> None:
    recs = [
        _rec("seo", "low", priority=Priority.LOW),
        _rec("seo", "high", priority=Priority.HIGH),
        _rec("seo", "critical", priority=Priority.CRITICAL),
        _rec("seo", "medium", priority=Priority.MEDIUM),
    ]
    ordered = prioritize(recs)
    assert [r.priority for r in ordered] == [
        Priority.CRITICAL,
        Priority.HIGH,
        Priority.MEDIUM,
        Priority.LOW,
    ]


def test_build_plan_summary_and_stats() -> None:
    recs = [
        _rec("seo", "Broken links"),
        _rec("seo", "Broken links"),
        _rec("ads", "High CPA"),
        _rec("ecommerce", "Stock-out", priority=Priority.CRITICAL),
    ]
    plan = build_plan(recs)
    stats = plan.stats()
    assert stats["total"] == 3
    assert stats["by_agent"] == {"seo": 1, "ads": 1, "ecommerce": 1}
    assert stats["by_priority"]["critical"] == 1
    assert plan.to_dict()["recommendations"][0]["priority"] == "critical"
