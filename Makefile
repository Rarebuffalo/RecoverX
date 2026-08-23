.PHONY: up down build logs test test-api seed migrate clean webhook-test evaluate

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-web:
	docker compose logs -f web

migrate:
	cd apps/api && alembic upgrade head

seed:
	cd apps/api && python3 -m app.db.seed

evaluate:
	cd apps/api && python3 -m app.scripts.evaluate_recovery

test: test-api

test-api:
	cd apps/api && pytest -v

webhook-test:
	cd apps/api && python3 -m app.scripts.send_test_webhook payment_failed.json

clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
