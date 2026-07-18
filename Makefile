# ── AI Data Analyst Agent ─────────────────────────────────────────────────────
.PHONY: help up down build migrate test logs clean

help:
	@echo ""
	@echo "  make up        Start all services (production)"
	@echo "  make dev       Start with hot-reload (development)"
	@echo "  make down      Stop all containers"
	@echo "  make build     Rebuild all images"
	@echo "  make migrate   Run database migrations"
	@echo "  make test      Run backend tests"
	@echo "  make logs      Tail all container logs"
	@echo "  make clean     Remove volumes and images"
	@echo ""

up:
	docker-compose up -d

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

down:
	docker-compose down

build:
	docker-compose build --no-cache

migrate:
	docker-compose exec backend alembic upgrade head

test:
	docker-compose exec backend pytest tests/ -v

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --rmi local
