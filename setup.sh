#!/bin/bash

# Setup script for E-commerce Data Warehouse CDC Project

set -e

echo "🚀 Starting E-commerce Data Warehouse Setup..."
echo ""

# Step 1: Start infrastructure
echo "📦 Step 1: Starting core infrastructure (Postgres, Kafka, Zookeeper)..."
docker-compose up -d postgres-source postgres-warehouse kafka zookeeper

echo "⏳ Waiting for services to be healthy (30 seconds)..."
sleep 30

# Step 2: Initialize warehouse schema
echo ""
echo "📊 Step 2: Initializing warehouse schema..."
docker exec -i postgres-warehouse psql -U postgres -d ecommerce_warehouse < warehouse_schema.sql
echo "✓ Warehouse schema created"

# Step 3: Wait for source database auto-initialization
echo ""
echo "⏳ Step 3: Waiting for source database to initialize..."
sleep 10
echo "✓ Source database ready"

# Step 4: Generate sample data
echo ""
echo "🎲 Step 4: Generating sample e-commerce data..."
if [ -d "cdc_env" ]; then
    source cdc_env/bin/activate
    python3 generate_data.py
    deactivate
else
    python3 generate_data.py
fi

# Step 5: Start Debezium Connect
echo ""
echo "🔌 Step 5: Starting Debezium Connect..."
docker-compose up -d connect

echo "⏳ Waiting for Debezium Connect to be ready (30 seconds)..."
sleep 30

# Step 6: Register Debezium connector
echo ""
echo "📡 Step 6: Registering CDC connector..."
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @debezium-config.json

echo ""
echo "✓ CDC connector registered"

# Step 7: Verify Kafka topics
echo ""
echo "📝 Step 7: Verifying Kafka topics..."
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list | grep ecommerce || echo "⚠ Topics not yet created (this is normal)"

# Step 8: Start ETL worker
echo ""
echo "⚙️ Step 8: Building and starting ETL worker..."
docker-compose up -d --build etl-worker

# Step 9: Start optional services
echo ""
echo "📓 Step 9: Starting Jupyter and Flask API..."
docker-compose up -d jupyter api

echo ""
echo "✅ Setup completed!"
echo ""
echo "📋 Services Status:"
docker-compose ps

echo ""
echo "🌐 Access URLs:"
echo "  - Source Database: localhost:5432 (user: postgres, db: ecommerce_source)"
echo "  - Warehouse Database: localhost:5433 (user: postgres, db: ecommerce_warehouse)"
echo "  - Jupyter Lab: http://localhost:8888"
echo "  - Flask API: http://localhost:5000"
echo "  - Debezium API: http://localhost:8083"
echo "  - Flink Dashboard: http://localhost:8081"
echo ""
echo "🔍 Check logs:"
echo "  docker-compose logs -f etl-worker"
echo ""
echo "🎬 Run demos:"
echo "  python3 demos/scenario_customer_change.py"
echo "  python3 demos/scenario_product_change.py"
echo "  python3 demos/scenario_order_placement.py"
echo ""
