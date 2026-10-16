"""Pytest suite for the Growth OS evaluation layer (also run by CI)."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.metrics import (
    cost_control,
    factual_accuracy,
    latency_budget,
    prompt_injection_resistance,
    recommendation_quality,
    tool_use_success,
)
from evaluation.run import _THRESHOLDS, run_suite


@pytest.fixture(scope="module")
def demo_result() -> dict:
    from demo.runner import run_demo

    return run_demo()


def test_all_datasets_present() -> None:
    expected = {
        "factual_accuracy.json",
        "tool_use_success.json",
        "recommendation_quality.json",
        "prompt_injection.json",
        "cost_latency.json",
    }
    files = {p.name for p in (Path(__file__).parent / "datasets").glob("*.json")}
    assert expected <= files


def test_factual_accuracy_threshold(demo_result: dict) -> None:
    score, _ = factual_accuracy(demo_result)
    assert score >= _THRESHOLDS["factual_accuracy"]


def test_tool_use_success_threshold(demo_result: dict) -> None:
    score, _ = tool_use_success(demo_result)
    assert score >= _THRESHOLDS["tool_use_success"]


def test_recommendation_quality_threshold(demo_result: dict) -> None:
    score, _ = recommendation_quality(demo_result)
    assert score >= _THRESHOLDS["recommendation_quality"]


def test_prompt_injection_threshold(demo_result: dict) -> None:
    score, _ = prompt_injection_resistance(demo_result)
    assert score >= _THRESHOLDS["prompt_injection_resistance"]


def test_cost_control_threshold(demo_result: dict) -> None:
    score, _ = cost_control(demo_result)
    assert score >= _THRESHOLDS["cost_control"]


def test_latency_threshold(demo_result: dict) -> None:
    score, _ = latency_budget(demo_result)
    assert score >= _THRESHOLDS["latency_budget"]


def test_suite_reports_all_metrics() -> None:
    scores = run_suite()
    assert set(scores) == set(_THRESHOLDS)
