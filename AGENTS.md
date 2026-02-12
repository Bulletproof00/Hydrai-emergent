# AGENTS.md

## Scope
This file applies to the entire repository.

## Conventions
- Python 3.12 only.
- Keep architecture modular: `apps/*` for entrypoints, `packages/*` for domain/application logic.
- UTC timestamps only.
- No live trading integration; paper signals only.
- Never hardcode secrets; use `.env`/secret manager.

## Commands
- `make up` start stack
- `make migrate` apply Alembic migrations
- `make seed` seed instruments
- `make lint` run static checks
- `make test` run tests

## Implementation notes
- Prefer idempotent workers and clear run tracking via `analysis_runs`.
- Keep API schemas stable and typed.
