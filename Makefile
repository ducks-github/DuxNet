.PHONY: help install install-dev setup test lint format clean docker-build docker-up docker-down docs

# Default target
help:
	@echo "DuxNet Development Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup:"
	@echo "  setup          - Run the automated setup script"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  format         - Format code with black and isort"
	@echo "  lint           - Run linting checks"
	@echo "  test           - Run tests"
	@echo "  test-cov       - Run tests with coverage"
	@echo "  docs           - Build documentation"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   - Build Docker images"
	@echo "  docker-up      - Start all services with Docker Compose"
	@echo "  docker-down    - Stop all Docker services"
	@echo ""
	@echo "Utilities:"
	@echo "  clean          - Clean up temporary files"
	@echo "  pre-commit     - Install pre-commit hooks"

# Setup and installation
setup:
	@echo "Running DuxNet setup..."
	./setup.sh

install:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt

# Code quality
format:
	@echo "Formatting code..."
	black .
	isort .

lint:
	@echo "Running linting checks..."
	flake8 .
	mypy .
	bandit -r . -f json -o bandit-report.json

# Testing
test:
	@echo "Running tests..."
	pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=. --cov-report=html --cov-report=term

# Documentation
docs:
	@echo "Building documentation..."
	cd docs && make html

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

# Utilities
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf build/
	rm -rf dist/
	rm -f bandit-report.json

pre-commit:
	@echo "Installing pre-commit hooks..."
	pre-commit install

# Service management
start-store:
	@echo "Starting store service..."
	python3 -m duxnet_store.main --config duxnet_store/config.yaml

start-task-engine:
	@echo "Starting task engine..."
	python3 -m duxos_tasks.main --config duxos_tasks/config.yaml

start-registry:
	@echo "Starting registry service..."
	python3 -m duxnet_registry.main --config duxnet_registry/config.yaml

start-wallet:
	@echo "Starting wallet service..."
	python3 -m duxnet_wallet.main --config duxnet_wallet/config.yaml

# Development server with hot reload
dev-store:
	@echo "Starting store service in development mode..."
	uvicorn duxnet_store.main:app --reload --host 0.0.0.0 --port 8000

dev-task-engine:
	@echo "Starting task engine in development mode..."
	uvicorn duxos_tasks.main:app --reload --host 0.0.0.0 --port 8001

# Database management
db-migrate:
	@echo "Running database migrations..."
	alembic upgrade head

db-rollback:
	@echo "Rolling back database migration..."
	alembic downgrade -1

# Security checks
security-check:
	@echo "Running security checks..."
	safety check
	bandit -r . -f json -o bandit-report.json

# Performance profiling
profile:
	@echo "Running performance profiling..."
	python -m py_spy top -- python3 -m duxnet_store.main

# Backup and restore
backup:
	@echo "Creating backup..."
	tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='.venv' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.git' \
		.

# Environment setup
env-setup:
	@echo "Setting up environment variables..."
	cp .env.example .env
	@echo "Please edit .env with your configuration"

# Git helpers
git-clean:
	@echo "Cleaning git repository..."
	git clean -fd
	git reset --hard HEAD

# Monitoring
monitor:
	@echo "Starting health monitor..."
	python3 health_monitor.py

# Quick development setup
quick-dev: install-dev pre-commit format lint test
	@echo "Quick development setup completed!"

# Production setup
prod-setup: install docker-build
	@echo "Production setup completed!" 