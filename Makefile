.PHONY: up down logs migrate seed test shell build clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.scripts.seed

test:
	docker compose exec backend pytest tests/ -v

shell:
	docker compose exec backend /bin/bash

clean:
	docker compose down -v --remove-orphans

ps:
	docker compose ps

worker-logs:
	docker compose logs -f worker

backend-logs:
	docker compose logs -f backend

restart:
	docker compose restart

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
