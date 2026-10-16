"""Integration tests: Growth OS imports and uses the shared package end-to-end."""

from __future__ import annotations

from ai_marketing_shared import __version__ as shared_version
from ai_marketing_shared.providers import ProviderFactory
from ai_marketing_shared.schemas import ApprovalItem, ApprovalStatus, Evidence, Recommendation
from ai_marketing_shared.tools import PermissionLevel
from ai_marketing_shared.tracing import Tracer


def test_shared_package_imported() -> None:
    assert shared_version.startswith("0.1")


def test_shared_schemas_round_trip() -> None:
    rec = Recommendation(
        agent="seo",
        issue="Broken links",
        proposed_action="fix 3 links",
        expected_impact="+5% organic clicks",
        evidence=[Evidence(source="website_crawl.csv", metric="broken_links", value=3)],
        requires_approval=True,
    )
    dumped = rec.model_dump(mode="json")
    restored = Recommendation.model_validate(dumped)
    assert restored == rec
    assert restored.requires_approval is True
    assert restored.status == ApprovalStatus.PENDING


def test_approval_item_schema_via_shared() -> None:
    item = ApprovalItem(recommendation_id="rec-1")
    assert item.status == ApprovalStatus.PENDING
    item.decide(approve=True, approver="ops-lead", outcome="approved in review")
    assert item.status == ApprovalStatus.APPROVED
    assert item.approver == "ops-lead"
    assert item.decided_at is not None


def test_provider_factory_defaults_to_mock() -> None:
    provider = ProviderFactory.get_provider()
    assert provider.provider_name == "mock"
    # Mock responses are cheap to generate; api_cost is zero.
    resp = provider.complete(prompt="hi")
    assert resp.api_cost == 0.0
    assert resp.usage_tokens > 0


def test_tracer_records_tool_calls() -> None:
    tracer = Tracer()
    run = tracer.start_run(agent="seo", input_summary="trace test")
    run.tool_calls.append(
        {
            "tool_name": "fetch_gsc_keywords",
            "arguments": {},
            "result_summary": "3 rows",
            "latency_ms": 1,
            "token_cost": 0,
            "success": True,
        }
    )
    tracer.complete_run(run)
    assert run.latency_ms >= 0
    assert run.status.value == "completed"


def test_permission_levels_are_comparable() -> None:
    # StrEnum members compare by value, so assert the escalation order explicitly.
    assert PermissionLevel.READ.value == "read"
    assert PermissionLevel.WRITE.value == "write"
    assert PermissionLevel.EXTERNAL.value == "external"
    assert [p.value for p in (PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXTERNAL)] == [
        "read",
        "write",
        "external",
    ]
