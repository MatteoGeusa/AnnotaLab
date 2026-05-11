# Makefile for AnnotaLab project

# Configuration
DB_COMPOSE_FILE = docker-compose-only-db.yaml
BACKEND_DIR = backend
# Using Windows paths for Python in venv
PYTHON = venv\Scripts\python

.PHONY: help db-up db-down server dev run migrate

help:
	@echo "AnnotaLab Management Commands:"
	@echo "  make db-up     - Start the database container"
	@echo "  make db-down   - Stop the database container"
	@echo "  make server    - Run the Django development server"
	@echo "  make dev       - Start database and then start the server"
	@echo "  make run       - Alias for make dev"
	@echo "  make migrate   - Apply Django migrations"

db-up:
	docker compose -f $(DB_COMPOSE_FILE) up -d

db-down:
	docker compose -f $(DB_COMPOSE_FILE) down

server:
	@echo "Starting Django server..."
	cd $(BACKEND_DIR) && $(PYTHON) manage.py runserver

migrate:
	@echo "Applying migrations..."
	cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate

dev: db-up
	@echo "Waiting for database to initialize..."
	@ping 127.0.0.1 -n 6 > nul
	$(MAKE) server

run: dev
