"""Unit tests for the FastAPI backend."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_agents_listing() -> None:
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    agents = resp.json()["agents"]
    assert set(agents) == {"seo", "ads", "ecommerce", "analytics"}


def test_demo_run_populates_queue() -> None:
    resp = client.post("/api/demo/run")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cost_usd"] == 0.0
    assert len(body["approval_queue"]) >= 8

    queue = client.get("/api/queue").json()
    assert queue["stats"]["pending"] == len(body["approval_queue"])


def test_approval_workflow_via_api() -> None:
    client.post("/api/demo/run")
    item_id = client.get("/api/queue").json()["items"][0]["id"]

    decided = client.post(f"/api/queue/{item_id}/decide", json={"approve": True, "approver": "tester"}).json()
    assert decided["status"] == "approved"

    executed = client.post(f"/api/queue/{item_id}/execute", json={"approver": "tester"}).json()
    assert executed["status"] == "executed"

    measured = client.post(f"/api/queue/{item_id}/measure", json={"outcome": "clicks +9%"}).json()
    assert measured["status"] == "measured"
    assert measured["outcome"] == "clicks +9%"


def test_approval_illegal_transition_returns_409() -> None:
    client.post("/api/demo/run")
    item_id = client.get("/api/queue").json()["items"][0]["id"]
    resp = client.post(f"/api/queue/{item_id}/execute", json={"approver": "tester"})
    assert resp.status_code == 409


def test_unknown_item_returns_404() -> None:
    resp = client.post("/api/queue/nope/decide", json={"approve": True})
    assert resp.status_code == 404


def test_runs_and_plan_endpoints() -> None:
    client.post("/api/demo/run")
    runs = client.get("/api/runs").json()["runs"]
    assert len(runs) == 4
    plan = client.get("/api/plan").json()["plan"]
    assert plan["stats"]["total"] >= 8
