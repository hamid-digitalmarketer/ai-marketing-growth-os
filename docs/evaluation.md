# Evaluation — ai-marketing-growth-os

## Methodology

Growth OS ships a reproducible evaluation suite that runs against the rule-based
demo pipeline. Because demo mode is deterministic and uses the mock provider,
scores are stable across machines and CI runs.

Metrics are functions of a live demo result and are enforced with labeled
datasets in `evaluation/datasets/`:

| Metric | What it measures | Labeled dataset | Threshold |
|---|---|---|---|
| factual_accuracy | produced recommendations match labeled (agent, issue, evidence-metric) cases | `factual_accuracy.json` | 1.0 |
| tool_use_success | tool call success rate + required-tool coverage per agent | `tool_use_success.json` | 1.0 |
| recommendation_quality | completeness of required fields + evidence + agent coverage | `recommendation_quality.json` | 0.9 |
| prompt_injection_resistance | adversarial summaries never trigger write tools; write tools denied at READ | `prompt_injection.json` | 1.0 |
| cost_control | demo cost stays at $0 with mock provider | `cost_latency.json` | 1.0 |
| latency_budget | whole-pipeline latency under budget | `cost_latency.json` | 1.0 |

## How to run

```bash
pip install -e ../ai-marketing-shared
pip install -e ".[dev]"
pytest evaluation/            # pytest suite (also covers the metrics)
python -m evaluation.run      # human-readable summary, exit code reflects pass/fail
```

## Metric details

### factual_accuracy
Each labeled case says "the `<agent>` agent must produce an issue containing
`<issue_contains>` with an evidence metric `<evidence_metric>`". The metric is
the fraction of cases satisfied by the demo run. This anchors agents to the
actual sample data — no invented numbers.

### tool_use_success
Checks that every tool call succeeded (`success=True`) and that each agent
called its required toolset (e.g., `seo` must call `fetch_website_crawl`,
`fetch_gsc_keywords`, `fetch_pagespeed`). The score is the minimum of the call
success rate and the required-tool coverage, so a missing tool lowers the
score.

### recommendation_quality
Every recommendation must include `issue`, `proposed_action`,
`expected_impact`, `next_steps`, at least one evidence item, and all four
agents must be present in the plan. Missing fields drop the score; the
threshold is 0.9 (the demo run scores 1.0).

### prompt_injection_resistance
Three adversarial summaries are fed through every agent; the suite verifies no
`execute_campaign_change` call is ever attempted (agents have no write tool in
their toolset), and that invoking the write tool at `READ` permission is
refused by the registry. This validates both the "agents can't even reach
write" and "write tool enforces least privilege" layers.

### cost_control & latency_budget
Demo mode uses `ProviderFactory.get_provider()` which defaults to the mock
provider (`api_cost_estimate = 0`), so `cost_usd == 0.0` always. Latency is
measured end-to-end over the demo run and must stay under the budget.

## Current results (demo mode)

Run `python -m evaluation.run` for the latest output. Expected on this
codebase: all six metrics meet their thresholds, `EVAL PASSED`.

## Baseline vs AI-based

The rule-based demo is the baseline; the architecture isolates provider
interfaces (`ProviderFactory`), so an LLM-backed variant can be evaluated with
the same datasets and harness by switching `AI_MARKETING_PROVIDER` — the
evaluation layer does not change.

## Coverage

Unit tests target core modules (`backend`, `agents`, `tools`, `orchestration`,
`demo`, `data.connectors`) with `pytest --cov-fail-under=80`; CI enforces the
same bar (see `.github/workflows/ci.yml`).
