.PHONY: help setup start stop restart logs clean test

help:
	@echo "E-commerce Data Warehouse - Make Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make setup       - Initial setup (run once)"
	@echo "  make start       - Start all services"
	@echo "  make stop        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs (all services)"
	@echo "  make logs-etl    - View ETL worker logs"
	@echo "  make logs-api    - View Flask API logs"
	@echo "  make test        - Test connections"
	@echo "  make clean       - Stop and remove all containers/volumes"
	@echo "  make demo        - Run all demo scenarios"
	@echo "  make status      - Show service status"

setup:
	@echo "Running setup script..."
	@bash setup.sh

start:
	@echo "Starting all services..."
	@docker-compose up -d

stop:
	@echo "Stopping all services..."
	@docker-compose stop

restart:
	@echo "Restarting all services..."
	@docker-compose restart

logs:
	@docker-compose logs -f

logs-etl:
	@docker-compose logs -f etl-worker

logs-api:
	@docker-compose logs -f api

test:
	@echo "Testing connections..."
	@python3 test_connection.py

clean:
	@echo "Cleaning up..."
	@docker-compose down -v
	@echo "All containers and volumes removed"

demo:
	@echo "Running demo scenarios..."
	@echo "\n=== Scenario 1: Customer Change ==="
	@python3 demos/scenario_customer_change.py
	@echo "\n=== Scenario 2: Product Change ==="
	@python3 demos/scenario_product_change.py
	@echo "\n=== Scenario 3: Order Placement ==="
	@python3 demos/scenario_order_placement.py

status:
	@docker-compose ps

build:
	@echo "Building Docker images..."
	@docker-compose build
