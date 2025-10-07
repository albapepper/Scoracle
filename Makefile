# Simple developer Makefile (POSIX environments)
# Usage examples:
#   make backend
#   make frontend
#   make up
#   make types

PYTHON=python
BACKEND_DIR=backend
VENV=$(BACKEND_DIR)/venv
UVICORN_PORT?=8000

.PHONY: backend frontend up types install-backend install-frontend

$(VENV):
	$(PYTHON) -m venv $(VENV)

install-backend: $(VENV)
	. $(VENV)/bin/activate; pip install -r $(BACKEND_DIR)/requirements.txt

install-frontend:
	cd frontend && [ -d node_modules ] || npm install

backend: install-backend
	. $(VENV)/bin/activate; UVICORN_WORKERS=1 uvicorn app.main:app --reload --port $(UVICORN_PORT)

frontend: install-frontend
	cd frontend && npm start

up: install-backend install-frontend
	( . $(VENV)/bin/activate; uvicorn app.main:app --reload --port $(UVICORN_PORT) ) & \
	( cd frontend && npm start )

types: install-frontend
	cd frontend && npm run api:types
