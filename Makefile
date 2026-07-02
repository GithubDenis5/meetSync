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

# ── Production helpers ──────────────────────────────────────────────

ssl-init: ## Generate self-signed SSL certificates (bootstrap)
	@echo "Initializing SSL certificates..."
	@sh scripts/init-ssl.sh

ssl-letsencrypt: ## Obtain/renew Let's Encrypt SSL certificates (usage: make ssl-letsencrypt DOMAIN=example.com)
	@if [ -z "$(DOMAIN)" ]; then \
		echo "Usage: make ssl-letsencrypt DOMAIN=example.com"; \
		exit 1; \
	fi
	sh scripts/ssl-letsencrypt.sh $(DOMAIN)

prod-build: ssl-init build ## Build all services with SSL certificates

prod-up: ## Start all services (production)
	docker compose up -d

prod-deploy: ssl-init build prod-up ## Full production deployment (bootstrap)

# ── Dev shortcuts ───────────────────────────────────────────────────

backup: ## Create a database backup
	docker compose exec pg-backup backup-db

restore: ## Restore database from backup (usage: make restore FILE=backup-file.sql.gz)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make restore FILE=backup-file.sql.gz"; \
		echo "Available backups:"; \
		docker compose exec pg-backup ls -lh /backups/postgres/; \
		exit 1; \
	fi
	docker compose exec pg-backup restore-db /backups/postgres/$(FILE)

shell-%: ## Open shell in a service (e.g. make shell-auth-service)
	docker compose exec $(subst shell-,,$@) sh

logs-%: ## Follow logs of a specific service (e.g. make logs-auth-service)
	docker compose logs -f $(subst logs-,,$@)

rebuild-%: ## Rebuild a specific service (e.g. make rebuild-auth-service)
	docker compose up -d --build $(subst rebuild-,,$@)
