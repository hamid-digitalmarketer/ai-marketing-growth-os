# Architecture — ai-marketing-growth-os

## Problem

Marketing teams run dozens of disconnected workflows: SEO audits, ad optimizations,
catalog management, and analytics reviews each live in separate tools, spreadsheets,
and opinions. Recommendations are rarely evidence-backed, and consequential actions
(publish, budget change, campaign edit) are taken without a governed approval path.

Growth OS is the flagship of the AI marketing portfolio: a single agentic
intelligence platform that behaves like a virtual digital marketing department —
four specialized agents produce evidence-backed recommendations, an orchestrator
deduplicates and prioritizes them into one unified action plan, and a
human-in-the-loop approval queue governs every consequential action.

## Design goals

1. **Evidence over opinion** — every recommendation cites data rows from sample
   exports (GA, GSC, Google Ads, Meta Ads, product catalog, PageSpeed, crawls).
2. **Tool-using agents** — agents never invent numbers; they read via read-only
   tools and surface what the data says.
3. **Structured outputs** — all agent outputs conform to shared Pydantic schemas
   (`Recommendation`, `Evidence`, `AgentRun`, `ToolCall`, `ApprovalItem`) from
   `ai-marketing-shared`.
4. **Human-in-the-loop** — no consequential action happens without approval;
   the queue state machine is `pending → approved/rejected → executed → measured`.
5. **Observability** — every run is traced with tool calls, latency, cost, and
   outcomes (trace viewer in the dashboard).
6. **Zero-API-key runnable** — rule-based demo mode + sample data + mock provider.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ frontend/ (static dashboard: recommendation cards, approval queue,  │
│           trace viewer)  ── served by FastAPI at /                  │
└───────────────┬─────────────────────────────────────────────────────┘
                │ JSON over HTTP
┌───────────────▼─────────────────────────────────────────────────────┐
│ backend/app.py (FastAPI)                                            │
│  /api/demo/run · /api/queue/{id}/decide|execute|measure ·           │
│  /api/runs · /api/plan · /api/agents                                 │
└───────────────┬─────────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────────┐
│ orchestration/                                                      │
│  planner.py      deduplicate → prioritize → unified plan            │
│  approval.py     approval queue state machine                       │
└───────────────┬─────────────────────────────────────────────────────┘
                │ recommendations + approval items
┌───────────────▼─────────────────────────────────────────────────────┐
│ agents/  (each: structured output, traced tool calls)               │
│  seo_agent.py       crawls + GSC + PageSpeed                         │
│  ads_agent.py       Google Ads + Meta Ads                            │
│  ecommerce_agent.py product catalog                                  │
│  analytics_agent.py GA sessions + GSC                                │
└───────────────┬─────────────────────────────────────────────────────┘
                │ read-only tool calls (PermissionLevel.READ)
┌───────────────▼─────────────────────────────────────────────────────┐
│ tools/                                                               │
│  data_tools.py    7 CSV-backed read tools                           │
│  write_tools.py   ExecuteCampaignChangeTool (WRITE, approval-gated) │
│  mcp_adapters.py  local MCP adapters (GoogleAds/MetaAds/GA4/GSC/…)  │
│  registry.py      ToolRegistry with permission enforcement          │
└───────────────┬─────────────────────────────────────────────────────┘
                │ local CSV sample data (zero API keys)
┌───────────────▼─────────────────────────────────────────────────────┐
│ data/sample_data/  crawls · GA · GSC · Ads · Meta · catalog · speed  │
└─────────────────────────────────────────────────────────────────────┘

Shared package (ai-marketing-shared): Pydantic schemas, BaseTool/PermissionLevel,
ToolRegistry, Tracer, ProviderFactory (mock default), cost accounting.
```

## Module responsibilities

### agents/
Each agent is a `BaseAgent` subclass with a defined toolset:

| Agent | Tools | Signals detected |
|---|---|---|
| `seo` | `fetch_website_crawl`, `fetch_gsc_keywords`, `fetch_pagespeed` | broken links, missing meta descriptions, low CTR, slow LCP |
| `ads` | `fetch_google_ads`, `fetch_meta_ads` | high CPA, low ROAS, pause-worthy campaigns |
| `ecommerce` | `fetch_product_catalog` | stock-out risk, low-inventory best sellers |
| `analytics` | `fetch_ga_sessions`, `fetch_gsc_keywords` | conversion decline, revenue drop |

Agents run `rule-based` logic over tool results and emit structured
`Recommendation` objects. They never call write tools; write access belongs to
the approval flow.

### tools/
- `data_tools.py` — read-only CSV-backed tools; data comes from
  `data/sample_data` (configurable via `GROWTH_OS_DATA_DIR`).
- `write_tools.py` — `ExecuteCampaignChangeTool` (WRITE); refused unless the
  caller holds WRITE permission; records a dry-run audit log in demo mode.
- `mcp_adapters.py` — thin local MCP adapters that present the same CSV data
  through a provider-shaped interface, mirroring how real Google Ads / Meta /
  GA4 / GSC MCP servers would be plugged in.
- `registry.py` — `build_registry()` wires all tools into a `ToolRegistry`
  that enforces permission levels.

### orchestration/
- `planner.py` — normalizes issues, deduplicates `(agent, issue)` pairs,
  sorts by priority (critical → low) then confidence, and builds a
  `UnifiedPlan` with per-agent / per-priority stats.
- `approval.py` — in-memory `ApprovalQueue` implementing the five-state
  machine with strict transition validation (illegal transitions raise).

### backend/
FastAPI app exposing the dashboard and API. In-memory demo store keeps the
pipeline stateless and safe to restart; the API surface is designed so a
PostgreSQL-backed store can replace it without changing endpoints.

### evaluation/
Labeled datasets + metric functions + pytest suite (see `docs/evaluation.md`).
CI runs the same checks; `python -m evaluation.run` prints a human-readable
summary and exits non-zero on failure.

## Tradeoffs and decisions

| Decision | Rationale | Cost |
|---|---|---|
| Rule-based demo mode as default | Zero API cost, deterministic CI, no secrets | No free-form LLM insight in demo |
| In-memory approval store | Simple, safe, stateless for demo | Not durable across restarts (swap for PostgreSQL in prod) |
| Static HTML frontend | Zero build step, served by FastAPI, portable | Less interactive than React/Next.js |
| Local MCP adapters | Prove the MCP interface without external servers | Adapters are thin by design |
| Shared schemas from `ai-marketing-shared` | Single source of truth across all portfolio repos | Requires sibling checkout to run locally |

## Data flow (demo run)

1. `POST /api/demo/run` → `demo.runner.run_demo()`
2. Each agent runs, calling read tools against sample CSVs; every call is
   traced into `AgentRun.tool_calls`.
3. Recommendations from all agents are collected, deduplicated, prioritized
   (`orchestration/planner.py`).
4. Each plan item is enqueued as `pending` (`orchestration/approval.py`).
5. Dashboard renders unified plan, approval queue, and trace viewer.
6. A user approves → executes → measures; state machine enforces order.

## Repository layout

See README for the full tree; key directories: `backend/`, `agents/`, `tools/`,
`data/`, `orchestration/`, `demo/`, `evaluation/`, `frontend/`, `infra/`,
`docs/`, `.github/workflows/`.
