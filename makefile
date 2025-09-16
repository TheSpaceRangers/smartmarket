PY=python
MANAGE=$(PY) src/manage.py

.PHONY: up
up:
	docker compose up -d db

.PHONY: migrate
migrate:
	$(MANAGE) migrate

.PHONY: seed-demo
seed-demo:
	$(MANAGE) seed_demo

.PHONY: seed-rbac
seed-rbac:
	$(MANAGE) bootstrap_rbac

.PHONY: dev
dev:
	$(MANAGE) runserver

.PHONY: test
test:
	pytest -q

.PHONY: lint
lint:
	ruff check .

.PHONY: fmt
fmt:
	black .
	ruff check --fix .