# AGENTS.md

## Scope
This file applies to the entire repository.

## Conventions
- Python 3.12 only.
- Keep architecture modular: `apps/*` entrypoints, `packages/*` logic.
- UTC timestamps only.
- No live trading integration; paper signals only.
- Never hardcode secrets; use encrypted DB storage via `CHAINALYZE_MASTER_KEY`.

## Commands
- `make up` start stack
- `make down` stop stack
- `make migrate` apply Alembic migrations
- `make seed` seed defaults
- `make lint` static checks
- `make fmt` auto-format
- `make test` run tests

## Implementation notes
- Prefer idempotent workers and explicit `analysis_runs` state transitions.
- API never returns secrets, only `secret_is_set` flags.
- Provider/Agent/Supervisor systems should remain plugin-friendly.
