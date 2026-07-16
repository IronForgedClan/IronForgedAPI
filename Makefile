.PHONY: up up-prod down test format shell migrate revision downgrade build-prod rmi-prod clean api-consumer-interactive api-consumer-list

up:
	docker compose up db api

up-prod:
	docker compose up db api_prod

down:
	docker compose down

test:
	python -m pip install -e .[dev]
	python run_tests.py

format:
	python -m black .

shell:
	docker compose run --rm api /bin/sh

migrate:
	docker compose run --rm api python -m alembic -c ironforgedcore/alembic.ini upgrade head

revision:
	docker compose run --rm api python -m alembic -c ironforgedcore/alembic.ini revision --autogenerate -m "$(DESC)"

downgrade:
	docker compose run --rm api python -m alembic -c ironforgedcore/alembic.ini downgrade -1

build-prod:
	docker compose build api_prod

rmi-prod:
	docker rmi ironforgedapi:prod

api-consumer-interactive:
	docker compose run --rm api python scripts/manage_api_consumers.py interactive

api-consumer-list:
	docker compose run --rm api python scripts/manage_api_consumers.py list

clean:
	docker compose down
	docker compose rm -f
	docker rmi ironforgedapi:prod
	docker system prune -f --volumes
	@echo "Cleanup complete!"
