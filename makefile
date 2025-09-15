PY=python
MANAGE=$(PY) src/manage.py

.PHONY: up migrate seed dev test lint fmt

up:
	docker compose up -d db

migrate:
	$(MANAGE) migrate

seed:
	$(MANAGE) seed_demo

dev:
	$(MANAGE) runserver

test:
	pytest -q

lint:
	ruff check .

fmt:
	black .
	ruff check --fix .