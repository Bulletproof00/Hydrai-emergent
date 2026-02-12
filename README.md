# CHAiNALYZE (Hydra AI) MVP

Institutional-style crypto market intelligence stack with modular agents, supervisors, reproducible runs, and a Streamlit dashboard.

## Architecture
- **API**: FastAPI (`apps/api`)
- **Worker**: Celery + Redis scheduler/queue (`apps/worker`)
- **UI**: Streamlit (`apps/ui`)
- **Core**: Settings, DB models, ingestion/analysis services (`packages/core`)
- **Agents**: Market structure, regime, derivatives stress, anomaly, macro stub (`packages/agents`)
- **Strategies**: Signal synthesis + supervisor checks (`packages/strategies`)
- **Observability**: structured logging, Prometheus endpoint (`packages/observability`)

## Why Celery?
Celery provides robust periodic scheduling (beat), retries, and scalable worker concurrency while fitting Redis-based MVP operations.

## Data flow
`MarketEvent (candles/funding/OI)` -> `Findings` -> `SupervisorReports` -> `Signals`

Each analysis run stores:
- `run_id` (uuid4)
- `config_hash`
- status transitions (`running -> completed/failed`)

## Quick start
```bash
cp .env.example .env
make up
make migrate
make seed
```

Services:
- API: http://localhost:8001
- Metrics: http://localhost:8001/metrics
- UI: http://localhost:8501

## Core endpoints
- `GET /health`
- `GET /instruments`
- `GET /candles?symbol=BTC/USDT&tf=5m`
- `GET /latest/findings?symbol=BTC/USDT`
- `GET /latest/signals?symbol=BTC/USDT`
- `GET /runs/{run_id}`
- `GET /metrics`

## Migrations
```bash
make migrate
```

## Tests & lint
```bash
make test
make lint
```

## Troubleshooting
- If worker cannot fetch exchange data, check outbound network/rate-limits.
- If migrations fail, ensure `db` is healthy and `POSTGRES_SYNC_DSN` points to reachable host.
- If UI is empty, run seed + wait for first ingest/analysis cycle.

## Scope guardrails
- No live trading order execution.
- Signals are paper-only.
- Secrets only through environment variables.
