"""Human-in-the-loop approval queue.

Implements the approval state machine
``pending -> approved/rejected -> executed -> measured``. Write actions are
never taken outside this queue: agents only produce recommendations, and
humans (or an automated executor with explicit rights) decide, execute, and
measure each one.
"""

from __future__ import annotations

from collections import Counter

from ai_marketing_shared.schemas import ApprovalItem, ApprovalStatus, Recommendation

_ALLOWED = {
    ApprovalStatus.PENDING: {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED},
    ApprovalStatus.APPROVED: {ApprovalStatus.EXECUTED},
    ApprovalStatus.EXECUTED: {ApprovalStatus.MEASURED},
    ApprovalStatus.REJECTED: set(),
    ApprovalStatus.MEASURED: set(),
}


class ApprovalQueue:
    """In-memory approval queue with strict state transitions."""

    def __init__(self) -> None:
        self._items: dict[str, ApprovalItem] = {}

    def enqueue(self, recommendation: Recommendation) -> ApprovalItem:
        """Add a recommendation to the queue as a pending item."""
        item = ApprovalItem(recommendation_id=recommendation.id)
        self._items[item.id] = item
        return item

    def enqueue_many(self, recommendations: list[Recommendation]) -> list[ApprovalItem]:
        return [self.enqueue(rec) for rec in recommendations]

    def get(self, item_id: str) -> ApprovalItem | None:
        return self._items.get(item_id)

    def list_items(self, status: ApprovalStatus | None = None) -> list[ApprovalItem]:
        items = list(self._items.values())
        if status is not None:
            items = [i for i in items if i.status == status]
        return sorted(items, key=lambda i: i.id)

    def decide(self, item_id: str, *, approve: bool, approver: str, outcome: str | None = None) -> ApprovalItem:
        item = self._require(item_id)
        target = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
        self._transition(item, target)
        item.decide(approve=approve, approver=approver, outcome=outcome)
        return item

    def execute(self, item_id: str, *, approver: str, outcome: str | None = None) -> ApprovalItem:
        item = self._require(item_id)
        self._transition(item, ApprovalStatus.EXECUTED)
        item.status = ApprovalStatus.EXECUTED
        item.approver = approver
        item.outcome = outcome or "executed"
        from ai_marketing_shared.schemas import utcnow

        item.decided_at = utcnow()
        return item

    def measure(self, item_id: str, *, outcome: str) -> ApprovalItem:
        item = self._require(item_id)
        self._transition(item, ApprovalStatus.MEASURED)
        item.status = ApprovalStatus.MEASURED
        item.outcome = outcome
        from ai_marketing_shared.schemas import utcnow

        item.decided_at = utcnow()
        return item

    def stats(self) -> dict[str, int]:
        counts = Counter(item.status for item in self._items.values())
        return {status.value: counts.get(status, 0) for status in ApprovalStatus}

    def _require(self, item_id: str) -> ApprovalItem:
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"Approval item not found: {item_id}")
        return item

    @staticmethod
    def _transition(item: ApprovalItem, target: ApprovalStatus) -> None:
        allowed = _ALLOWED.get(item.status, set())
        if target not in allowed:
            raise ValueError(
                f"Illegal transition {item.status.value} -> {target.value} for item {item.id}"
            )
