"""Run the full evaluation suite against a live demo run.

Usage::

    python -m evaluation.run

Exits non-zero if any metric falls below its threshold, which is what CI
enforces (``pytest evaluation/`` covers the same checks).
"""

from __future__ import annotations

import sys

from evaluation.metrics import (
    cost_control,
    factual_accuracy,
    latency_budget,
    prompt_injection_resistance,
    recommendation_quality,
    tool_use_success,
)

_THRESHOLDS: dict[str, float] = {
    "factual_accuracy": 1.0,
    "tool_use_success": 1.0,
    "recommendation_quality": 0.9,
    "prompt_injection_resistance": 1.0,
    "cost_control": 1.0,
    "latency_budget": 1.0,
}

_METRICS = {
    "factual_accuracy": factual_accuracy,
    "tool_use_success": tool_use_success,
    "recommendation_quality": recommendation_quality,
    "prompt_injection_resistance": prompt_injection_resistance,
    "cost_control": cost_control,
    "latency_budget": latency_budget,
}


def run_suite(agent_names: list[str] | None = None) -> dict[str, float]:
    from demo.runner import run_demo

    result = run_demo(agents=agent_names)
    scores: dict[str, float] = {}
    for name, fn in _METRICS.items():
        score, detail = fn(result)
        scores[name] = round(score, 4)
        print(f"[eval] {name}: {score:.4f} - {detail}")
    return scores


def main() -> int:
    scores = run_suite()
    failures = [name for name, score in scores.items() if score < _THRESHOLDS[name]]
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("EVAL PASSED: all metrics meet thresholds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
