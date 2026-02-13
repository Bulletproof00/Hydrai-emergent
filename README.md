# CHAiNALYZE (Hydra AI) – Baukasten MVP

Production-style, self-hostable market intelligence system (no live trading) with configurable providers, agent prompts, schedules, and encrypted secrets managed from UI.

## Stack
- Python 3.12, FastAPI, Streamlit
- PostgreSQL + Redis
- Celery Worker + Beat
- SQLAlchemy + Alembic
- Structlog + Prometheus metrics

## Milestones delivered
- **M1**: scaffold, docker, `/health`, Streamlit shell
- **M2**: DB models + migrations + seed defaults
- **M3**: provider plugin system (Binance, DemoCSV, GenericHTTP stub), ingestion service
- **M4/M5**: deterministic agents, findings/signals, supervisors
- **M6**: API/UI Baukasten CRUD for providers, llm, agents, instruments, app-settings, alerts
- **M7 (MVP stub)**: Gemini client interface + schema validator + write-only secret flows

## Security model
Only these env values are required post-boot:
- `CHAINALYZE_MASTER_KEY`
- DB/Redis URLs

All provider/LLM/alert secrets are encrypted in DB and never returned via API/UI (only `secret_is_set`).

## Run
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

## Key API endpoints
- `GET /health`
- `GET/POST /app-settings`
- `GET/POST/PUT /providers`, `POST /providers/{id}/test`
- `GET/POST /llm`, `POST /llm/test`
- `GET /agents`, `PUT /agents/{name}`, `GET /agents/{name}/versions`, `POST /agents/{name}/version`, `POST /agents/{name}/rollback`
- `GET/POST /instruments`, `POST /instruments/{id}/assign-provider`
- `GET /candles`
- `GET /runs`, `GET /runs/{run_id}`, `POST /runs/trigger`
- `GET /latest/findings`, `GET /latest/signals`
- `GET/POST /alerts/config`, `POST /alerts/test`

## Offline capability
`DemoCSVProvider` reads `/data/*.csv` so XAU/XAG/SPX (and optionally crypto) can run end-to-end without external paid feeds.

## Notes
- Deterministic analysis works without LLM enabled.
- Gemini integration in this environment is implemented as a safe stub client path for offline runs.
