# Cost Controls — ai-marketing-growth-os

## Zero-cost demo mode

Growth OS runs end-to-end with **zero API keys and zero cost**:

- `AI_MARKETING_PROVIDER=mock` (default) — `ProviderFactory.get_provider()`
  returns the mock provider; every provider call reports
  `api_cost_estimate = 0.0`.
- All tools read local sample CSVs in `data/sample_data/` — no external calls,
  no network, no rate limits.
- The evaluation suite and CI run entirely in demo mode, so contributors and
  recruiters can verify the system without spending anything.

## Cost caps (for non-demo providers)

When you opt into a real provider (`AI_MARKETING_PROVIDER=openai|anthropic`):

1. Set `AI_MARKETING_COST_CAP_USD` in `.env` (default `1.0`).
2. The shared cost-accounting utilities (`ai-marketing-shared.cost`) record
   token and API cost per run; the run result carries `api_cost_estimate`.
3. Agents in this repo are **rule-based by design** even in provider mode for
   core signals — providers are optional enhancements, never required paths.

## Least-privilege tools

- Read tools (`fetch_*`) require `PermissionLevel.READ`.
- `execute_campaign_change` requires `PermissionLevel.WRITE` and is **never
  invoked by agents**; direct invocation at READ is refused by the registry
  (covered by `prompt_injection_resistance`).
- No secrets are hardcoded; `.env.example` documents every variable.

## Rate and budget hygiene

- Demo mode: no external rate limits apply.
- Non-demo mode: keep API keys in `.env` (git-ignored), cap per-run cost, and
  rely on the shared fallback engine for provider failures.

## Why this matters

The portfolio standard is *"runnable with zero API keys"*: anyone cloning the
repo can run `docker compose up` and see the full pipeline — evidence-backed
recommendations, approval queue, trace viewer — without touching a cloud
account.
