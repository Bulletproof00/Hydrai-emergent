.PHONY: up down migrate seed test lint fmt logs

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

fmt:
	black . && ruff check . --fix

logs:
	docker compose logs -f --tail=200
