# Dev only. Requires the bot repo at $(BOT_DIR) for the shared dev database.
# Override the path: make up BOT_DIR=/path/to/IronForgedBot
BOT_DIR ?= ../IronForgedBot

.PHONY: up up-prod down down-all test format shell migrate revision downgrade build-prod rmi-prod clean api-consumer-interactive api-consumer-list db-logs db-shell

up:
	@if [ ! -d "$(BOT_DIR)" ]; then \
		echo "Bot repo not found at $(BOT_DIR). Clone it or set BOT_DIR=... (e.g. 'make up BOT_DIR=/path/to/IronForgedBot')."; \
		exit 1; \
	fi
	@if [ -z "$$(docker ps --filter name=ironforged_db --format '{{.Names}}')" ]; then \
		echo "Starting shared dev db from $(BOT_DIR)..."; \
		docker compose -f $(BOT_DIR)/docker-compose.yml up -d db; \
	fi
	@bash -c 'i=0; until [ "$$(docker inspect --format "{{.State.Health.Status}}" ironforged_db 2>/dev/null)" = "healthy" ] || [ "$$i" -ge 30 ]; do sleep 2; i=$$((i+1)); done; if [ "$$i" -ge 30 ]; then echo "Db failed to become healthy in 60s"; exit 1; fi'
	docker compose up -d api

up-prod:
	docker compose up -d api_prod

down:
	docker compose down

down-all:
	docker compose -f $(BOT_DIR)/docker-compose.yml down
	docker compose down

test:
	python -m pip install -e .[dev]
	python run_tests.py

format:
	python -m black .

shell:
	docker compose run --rm api /bin/sh

migrate:
	docker compose run --rm api alembic -c /usr/local/lib/python3.13/site-packages/ironforgedcore/alembic.ini upgrade head

revision:
	docker compose run --rm api alembic -c /usr/local/lib/python3.13/site-packages/ironforgedcore/alembic.ini revision --autogenerate -m "$(DESC)"

downgrade:
	docker compose run --rm api alembic -c /usr/local/lib/python3.13/site-packages/ironforgedcore/alembic.ini downgrade -1

build-prod:
	docker compose build api_prod

rmi-prod:
	docker rmi ironforgedapi:prod

api-consumer-interactive:
	docker compose run --rm api python scripts/manage_api_consumers.py interactive

api-consumer-list:
	docker compose run --rm api python scripts/manage_api_consumers.py list

db-logs:
	docker compose -f $(BOT_DIR)/docker-compose.yml logs -f db

db-shell:
	docker compose -f $(BOT_DIR)/docker-compose.yml exec db mariadb -u"$$DB_USER" -p"$$DB_PASS" "$$DB_NAME"

clean:
	docker compose down
	docker compose rm -f
	docker rmi ironforgedapi:prod
	docker system prune -f --volumes
	@echo "Cleanup complete!"
