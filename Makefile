.PHONY: help build up down restart logs ps clean migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all services
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

restart: down up ## Restart all services

logs: ## Follow logs of all services
	docker compose logs -f

ps: ## Show service status
	docker compose ps

clean: ## Stop and remove volumes
	docker compose down -v

migrate: ## Run alembic migrations on all services
	@echo "Running migrations..."
	@for service in auth user group calendar ideas voting; do \
		echo "Migrating $$service-service..."; \
		docker compose exec $$service-service alembic upgrade head || true; \
	done

shell-%: ## Open shell in a service (e.g. make shell-auth-service)
	docker compose exec $(subst shell-,,$@) sh

logs-%: ## Follow logs of a specific service (e.g. make logs-auth-service)
	docker compose logs -f $(subst logs-,,$@)

rebuild-%: ## Rebuild a specific service (e.g. make rebuild-auth-service)
	docker compose up -d --build $(subst rebuild-,,$@)
