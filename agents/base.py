"""Base agent framework for Growth OS.

Every agent:
- resolves tools through the shared registry at READ permission in demo mode;
- records a full :class:`AgentRun` trace (tool calls, latency, recommendations);
- returns structured :class:`Recommendation` objects backed by :class:`Evidence`.

Providers are abstracted through ``ai_marketing_shared.providers`` so the same
agents can run with a mock (zero cost), OpenAI, or Anthropic provider.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from ai_marketing_shared.schemas import (
    AgentRun,
    AgentStatus,
    Confidence,
    Effort,
    Evidence,
    Priority,
    Recommendation,
    ToolCall,
)
from ai_marketing_shared.tools import PermissionLevel, ToolRegistry
from ai_marketing_shared.tracing import Tracer


class BaseAgent(ABC):
    """Abstract marketing agent with tool access and structured outputs."""

    name: str = "base"
    description: str = ""
    tools: tuple[str, ...] = ()

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        tracer: Tracer | None = None,
        allowed_permission: PermissionLevel = PermissionLevel.READ,
    ) -> None:
        self.registry = registry
        self.tracer = tracer or Tracer()
        self.allowed_permission = allowed_permission

    @abstractmethod
    def _collect(self, run: AgentRun) -> dict[str, Any]:
        """Call tools and return structured facts used by the rules."""

    @abstractmethod
    def _analyze(self, data: dict[str, Any]) -> list[Recommendation]:
        """Turn facts into evidence-backed recommendations."""

    def run(self, *, input_summary: str = "") -> AgentRun:
        """Execute one agent run and return a complete, observable trace."""
        run = self.tracer.start_run(agent=self.name, input_summary=input_summary)
        try:
            data = self._collect(run)
            run.recommendations = self._analyze(data)
            run.api_cost_estimate = 0.0
            self.tracer.complete_run(run)
        except Exception as exc:  # pragma: no cover - defensive
            self.tracer.complete_run(run, status=AgentStatus.FAILED, error=str(exc))
        return run

    def _call_tool(self, run: AgentRun, name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a registry tool, trace the call, and return its data dict."""
        started = time.perf_counter()
        result = self.registry.execute(
            name, allowed_permission=self.allowed_permission, **kwargs
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if result is None:
            run.tool_calls.append(
                ToolCall(
                    tool_name=name,
                    arguments=kwargs,
                    result_summary="Unknown tool",
                    latency_ms=latency_ms,
                    success=False,
                    error="Tool not found in registry",
                )
            )
            return {}
        run.tool_calls.append(
            ToolCall(
                tool_name=name,
                arguments=kwargs,
                result_summary=result.summary,
                latency_ms=latency_ms,
                success=result.success,
                error=result.error,
            )
        )
        if not result.success:
            return {}
        return result.data

    @staticmethod
    def _evidence(source: str, metric: str, value: float) -> Evidence:
        return Evidence(source=source, metric=metric, value=value)

    @staticmethod
    def _recommendation(
        *,
        agent: str,
        issue: str,
        evidence: list[Evidence],
        proposed_action: str,
        priority: Priority = Priority.MEDIUM,
        confidence: Confidence = Confidence.MEDIUM,
        expected_impact: str = "",
        effort: Effort = Effort.MEDIUM,
        next_steps: list[str] | None = None,
    ) -> Recommendation:
        return Recommendation(
            agent=agent,
            issue=issue,
            evidence=evidence,
            priority=priority,
            confidence=confidence,
            expected_impact=expected_impact,
            effort=effort,
            proposed_action=proposed_action,
            next_steps=next_steps or [],
            requires_approval=True,
        )
