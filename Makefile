.PHONY: up down migrate seed test lint

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	alembic upgrade head

seed:
	python infra/scripts/seed_instruments.py

test:
	pytest -q

lint:
	ruff check . && black --check .
