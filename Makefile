.PHONY: help build up down logs shell clean rebuild status

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)HR System - Docker Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo "  make build      - Build Docker image"
	@echo "  make up         - Start containers"
	@echo "  make down       - Stop containers"
	@echo "  make logs       - View container logs"
	@echo "  make shell      - Open shell in container"
	@echo "  make clean      - Remove containers and images"
	@echo "  make rebuild    - Rebuild and restart"
	@echo "  make status     - Show container status"
	@echo ""

build:
	@echo "$(GREEN)[1/1] Building Docker image...$(NC)"
	docker-compose build
	@echo "$(GREEN)[OK] Build complete!$(NC)"

up:
	@echo "$(GREEN)[1/1] Starting containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)[OK] Containers started!$(NC)"
	@echo "$(YELLOW)Access at: http://localhost:5000$(NC)"

down:
	@echo "$(RED)[1/1] Stopping containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)[OK] Containers stopped!$(NC)"

logs:
	docker-compose logs -f hr-system

shell:
	docker-compose exec hr-system /bin/bash

clean:
	@echo "$(RED)[1/3] Stopping containers...$(NC)"
	docker-compose down
	@echo "$(RED)[2/3] Removing images...$(NC)"
	docker-compose down --rmi all
	@echo "$(RED)[3/3] Removing volumes...$(NC)"
	docker volume prune -f
	@echo "$(GREEN)[OK] Cleanup complete!$(NC)"

rebuild: clean build up
	@echo "$(GREEN)[OK] Rebuild complete!$(NC)"

status:
	@echo "$(GREEN)Container Status:$(NC)"
	docker-compose ps
	@echo ""
	@echo "$(GREEN)Image Information:$(NC)"
	docker images | grep hr-system