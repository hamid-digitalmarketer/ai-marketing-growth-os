# Multi-stage build for ai-marketing-growth-os.
# Build context must be the ai_portfolio root (parent of both this repo and
# ai-marketing-shared); see infra/docker-compose.yml.

FROM python:3.11-slim AS builder

WORKDIR /build

# Shared package first (cached layer).
COPY ai-marketing-shared/ /build/ai-marketing-shared/
RUN pip install --no-cache-dir /build/ai-marketing-shared

# Flagship app.
COPY ai-marketing-growth-os/ /build/app/
WORKDIR /build/app
RUN pip install --no-cache-dir .

FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /build/app /app

ENV AI_MARKETING_PROVIDER=mock
EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
