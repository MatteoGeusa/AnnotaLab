# Makefile for AnnotaLab project

# Configuration
DB_COMPOSE_FILE = docker-compose-only-db.yaml
BACKEND_DIR = backend
# Using Windows paths for Python in venv
PYTHON = venv\Scripts\python

.PHONY: help db-up db-down server dev

help:
	@echo "AnnotaLab Management Commands:"
	@echo "  make db-up     - Start the database container"
	@echo "  make db-down   - Stop the database container"
	@echo "  make server    - Run the Django development server"
	@echo "  make dev       - Start database and then start the server"

db-up:
	docker compose -f $(DB_COMPOSE_FILE) up -d

db-down:
	docker compose -f $(DB_COMPOSE_FILE) down

server:
	@echo "Starting Django server..."
	cd $(BACKEND_DIR) && $(PYTHON) manage.py runserver

dev: db-up server
