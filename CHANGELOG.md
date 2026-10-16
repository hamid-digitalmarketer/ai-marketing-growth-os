# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-16

### Added
- Four marketing agents (SEO, Ads, E-commerce, Analytics) with structured,
  evidence-backed outputs built on `ai-marketing-shared` Pydantic schemas.
- Tool layer with permission-gated `BaseTool` implementations over local sample
  data, plus concrete MCP adapter stubs for Google Ads, Meta Ads, GA4, GSC, and web crawl.
- Orchestration layer: recommendation deduplication, priority ranking, and a
  unified action plan builder.
- Human-in-the-loop approval queue with the
  `pending -> approved -> rejected -> executed -> measured` state machine
  (FastAPI backend endpoints).
- Rule-based demo mode: end-to-end pipeline with zero API keys and zero cost.
- Evaluation suite: factual accuracy, tool-use success, recommendation quality,
  prompt-injection resistance, cost, and latency (labeled JSONL datasets + pytest).
- Docker multi-stage build and `docker compose up` support.
- Lightweight static dashboard (dashboard, approval queue, trace viewer,
  recommendation cards) served by the FastAPI app.
- CI (GitHub Actions): ruff lint, mypy type-check, pytest + coverage, eval, docker build.
- Docs: architecture, evaluation methodology, cost controls.
