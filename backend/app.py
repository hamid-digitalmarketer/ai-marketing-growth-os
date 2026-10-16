"""Growth OS FastAPI application.

Exposes the demo pipeline, approval queue state machine, and trace viewer data.
The app is stateless across restarts (in-memory demo store); production would
swap the store for PostgreSQL via the same API surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_marketing_shared.schemas import ApprovalStatus, utcnow
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from demo.runner import build_agents, run_demo
from orchestration.approval import ApprovalQueue

app = FastAPI(
    title="ai-marketing-growth-os",
    description="Agentic marketing intelligence platform - virtual digital marketing department.",
    version="0.1.0",
)

# In-memory demo store (replaced by PostgreSQL in production).
_STORE: dict[str, Any] = {
    "queue": ApprovalQueue(),
    "runs": [],
    "plan": None,
    "last_run_at": None,
}


class DecideRequest(BaseModel):
    approve: bool
    approver: str = Field(default="ops-lead", min_length=1, max_length=64)
    outcome: str | None = Field(default=None, max_length=256)


class ExecuteRequest(BaseModel):
    approver: str = Field(default="ops-lead", min_length=1, max_length=64)
    outcome: str | None = Field(default=None, max_length=256)


class MeasureRequest(BaseModel):
    outcome: str = Field(min_length=1, max_length=256)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-marketing-growth-os", "ts": utcnow().isoformat()}


@app.get("/api/agents")
def agents() -> dict[str, Any]:
    return {"agents": {name: agent.description for name, agent in build_agents().items()}}


@app.post("/api/demo/run")
def demo_run(agent_names: list[str] | None = None) -> dict[str, Any]:
    result = run_demo(agents=agent_names)
    _STORE["runs"] = result["agent_runs"]
    _STORE["plan"] = result["plan"]
    _rebuild_queue()
    _STORE["last_run_at"] = utcnow().isoformat()
    return result


def _rebuild_queue() -> None:
    queue = ApprovalQueue()
    if _STORE["plan"] is None:
        return
    from ai_marketing_shared.schemas import Recommendation

    for rec_dict in _STORE["plan"]["recommendations"]:
        queue.enqueue(Recommendation.model_validate(rec_dict))
    _STORE["queue"] = queue


@app.get("/api/queue")
def list_queue(status: str | None = None) -> dict[str, Any]:
    parsed = None
    if status is not None:
        try:
            parsed = ApprovalStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}") from exc
    items = _STORE["queue"].list_items(parsed)
    return {
        "items": [item.model_dump(mode="json") for item in items],
        "stats": _STORE["queue"].stats(),
    }


@app.post("/api/queue/{item_id}/decide")
def decide_item(item_id: str, body: DecideRequest) -> dict[str, Any]:
    try:
        item = _STORE["queue"].decide(
            item_id, approve=body.approve, approver=body.approver, outcome=body.outcome
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 409, detail=str(exc)) from exc
    return item.model_dump(mode="json")


@app.post("/api/queue/{item_id}/execute")
def execute_item(item_id: str, body: ExecuteRequest) -> dict[str, Any]:
    try:
        item = _STORE["queue"].execute(item_id, approver=body.approver, outcome=body.outcome)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 409, detail=str(exc)) from exc
    return item.model_dump(mode="json")


@app.post("/api/queue/{item_id}/measure")
def measure_item(item_id: str, body: MeasureRequest) -> dict[str, Any]:
    try:
        item = _STORE["queue"].measure(item_id, outcome=body.outcome)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 409, detail=str(exc)) from exc
    return item.model_dump(mode="json")


@app.get("/api/runs")
def list_runs() -> dict[str, Any]:
    return {"runs": _STORE["runs"]}


@app.get("/api/plan")
def current_plan() -> dict[str, Any]:
    if _STORE["plan"] is None:
        return {"plan": None, "message": "Run the demo pipeline first (POST /api/demo/run)."}
    return {"plan": _STORE["plan"]}


# Serve the static dashboard at / (registered last so API routes win).
_FRONTEND_DIR = (Path(__file__).resolve().parents[1] / "frontend")
if _FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
