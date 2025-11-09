#!/bin/bash

# Setup script for CDC Tutorial with Realistic Data
# This script automates the setup process described in TUTORIAL_SCHEMA_EVOLUTION.md

set -e  # Exit on error

echo "========================================================================"
echo "  CDC Tutorial Setup: Initial Snapshot + Streaming + Schema Evolution"
echo "========================================================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo
    echo -e "${GREEN}▶ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Step 1: Start Docker services
print_step "Step 1: Starting Docker Compose services..."
docker-compose up -d

print_info "Waiting 15 seconds for services to be ready..."
sleep 15

# Verify all services are running
print_step "Verifying services..."
docker-compose ps

# Step 2: Create PostgreSQL table
print_step "Step 2: Creating PostgreSQL customers table..."
docker exec postgres psql -U postgres << 'EOF'
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\d customers
EOF

print_success "PostgreSQL table created"

# Step 3: Populate MySQL with realistic data
print_step "Step 3: Populating MySQL with 100 realistic customers..."
docker exec -it mysql mysql -umysqluser -pmysqlpw << 'EOF'
USE inventory;

-- Clear existing data
TRUNCATE TABLE customers;

-- Insert 100 realistic customers
INSERT INTO customers (id, first_name, last_name, email) VALUES
(1001, 'Emma', 'Johnson', 'emma.johnson@email.com'),
(1002, 'Liam', 'Williams', 'liam.williams@email.com'),
(1003, 'Olivia', 'Brown', 'olivia.brown@email.com'),
(1004, 'Noah', 'Jones', 'noah.jones@email.com'),
(1005, 'Ava', 'Garcia', 'ava.garcia@email.com'),
(1006, 'Ethan', 'Miller', 'ethan.miller@email.com'),
(1007, 'Sophia', 'Davis', 'sophia.davis@email.com'),
(1008, 'Mason', 'Rodriguez', 'mason.rodriguez@email.com'),
(1009, 'Isabella', 'Martinez', 'isabella.martinez@email.com'),
(1010, 'William', 'Hernandez', 'william.hernandez@email.com'),
(1011, 'Mia', 'Lopez', 'mia.lopez@email.com'),
(1012, 'James', 'Gonzalez', 'james.gonzalez@email.com'),
(1013, 'Charlotte', 'Wilson', 'charlotte.wilson@email.com'),
(1014, 'Benjamin', 'Anderson', 'benjamin.anderson@email.com'),
(1015, 'Amelia', 'Thomas', 'amelia.thomas@email.com'),
(1016, 'Lucas', 'Taylor', 'lucas.taylor@email.com'),
(1017, 'Harper', 'Moore', 'harper.moore@email.com'),
(1018, 'Henry', 'Jackson', 'henry.jackson@email.com'),
(1019, 'Evelyn', 'Martin', 'evelyn.martin@email.com'),
(1020, 'Alexander', 'Lee', 'alexander.lee@email.com'),
(1021, 'Abigail', 'Perez', 'abigail.perez@email.com'),
(1022, 'Michael', 'Thompson', 'michael.thompson@email.com'),
(1023, 'Emily', 'White', 'emily.white@email.com'),
(1024, 'Daniel', 'Harris', 'daniel.harris@email.com'),
(1025, 'Elizabeth', 'Sanchez', 'elizabeth.sanchez@email.com'),
(1026, 'Matthew', 'Clark', 'matthew.clark@email.com'),
(1027, 'Sofia', 'Ramirez', 'sofia.ramirez@email.com'),
(1028, 'Joseph', 'Lewis', 'joseph.lewis@email.com'),
(1029, 'Avery', 'Robinson', 'avery.robinson@email.com'),
(1030, 'David', 'Walker', 'david.walker@email.com'),
(1031, 'Ella', 'Young', 'ella.young@email.com'),
(1032, 'Jackson', 'Allen', 'jackson.allen@email.com'),
(1033, 'Scarlett', 'King', 'scarlett.king@email.com'),
(1034, 'Sebastian', 'Wright', 'sebastian.wright@email.com'),
(1035, 'Victoria', 'Scott', 'victoria.scott@email.com'),
(1036, 'Aiden', 'Torres', 'aiden.torres@email.com'),
(1037, 'Grace', 'Nguyen', 'grace.nguyen@email.com'),
(1038, 'Samuel', 'Hill', 'samuel.hill@email.com'),
(1039, 'Chloe', 'Flores', 'chloe.flores@email.com'),
(1040, 'John', 'Green', 'john.green@email.com'),
(1041, 'Aria', 'Adams', 'aria.adams@email.com'),
(1042, 'Christopher', 'Nelson', 'christopher.nelson@email.com'),
(1043, 'Camila', 'Baker', 'camila.baker@email.com'),
(1044, 'Andrew', 'Hall', 'andrew.hall@email.com'),
(1045, 'Luna', 'Rivera', 'luna.rivera@email.com'),
(1046, 'Joshua', 'Campbell', 'joshua.campbell@email.com'),
(1047, 'Penelope', 'Mitchell', 'penelope.mitchell@email.com'),
(1048, 'Ryan', 'Carter', 'ryan.carter@email.com'),
(1049, 'Layla', 'Roberts', 'layla.roberts@email.com'),
(1050, 'Nathan', 'Gomez', 'nathan.gomez@email.com'),
(1051, 'Zoey', 'Phillips', 'zoey.phillips@email.com'),
(1052, 'Isaac', 'Evans', 'isaac.evans@email.com'),
(1053, 'Nora', 'Turner', 'nora.turner@email.com'),
(1054, 'Gabriel', 'Diaz', 'gabriel.diaz@email.com'),
(1055, 'Lily', 'Parker', 'lily.parker@email.com'),
(1056, 'Dylan', 'Cruz', 'dylan.cruz@email.com'),
(1057, 'Zoe', 'Edwards', 'zoe.edwards@email.com'),
(1058, 'Owen', 'Collins', 'owen.collins@email.com'),
(1059, 'Hannah', 'Reyes', 'hannah.reyes@email.com'),
(1060, 'Carter', 'Stewart', 'carter.stewart@email.com'),
(1061, 'Lillian', 'Morris', 'lillian.morris@email.com'),
(1062, 'Wyatt', 'Morales', 'wyatt.morales@email.com'),
(1063, 'Addison', 'Murphy', 'addison.murphy@email.com'),
(1064, 'Luke', 'Cook', 'luke.cook@email.com'),
(1065, 'Ellie', 'Rogers', 'ellie.rogers@email.com'),
(1066, 'Jayden', 'Gutierrez', 'jayden.gutierrez@email.com'),
(1067, 'Natalie', 'Ortiz', 'natalie.ortiz@email.com'),
(1068, 'Levi', 'Morgan', 'levi.morgan@email.com'),
(1069, 'Aubrey', 'Cooper', 'aubrey.cooper@email.com'),
(1070, 'Grayson', 'Peterson', 'grayson.peterson@email.com'),
(1071, 'Hazel', 'Bailey', 'hazel.bailey@email.com'),
(1072, 'Julian', 'Reed', 'julian.reed@email.com'),
(1073, 'Stella', 'Kelly', 'stella.kelly@email.com'),
(1074, 'Mateo', 'Howard', 'mateo.howard@email.com'),
(1075, 'Eliana', 'Ramos', 'eliana.ramos@email.com'),
(1076, 'Anthony', 'Kim', 'anthony.kim@email.com'),
(1077, 'Paisley', 'Cox', 'paisley.cox@email.com'),
(1078, 'Lincoln', 'Ward', 'lincoln.ward@email.com'),
(1079, 'Violet', 'Richardson', 'violet.richardson@email.com'),
(1080, 'Joshua', 'Watson', 'joshua.watson@email.com'),
(1081, 'Aurora', 'Brooks', 'aurora.brooks@email.com'),
(1082, 'Christopher', 'Chavez', 'christopher.chavez@email.com'),
(1083, 'Savannah', 'Wood', 'savannah.wood@email.com'),
(1084, 'Eli', 'James', 'eli.james@email.com'),
(1085, 'Brooklyn', 'Bennett', 'brooklyn.bennett@email.com'),
(1086, 'Thomas', 'Gray', 'thomas.gray@email.com'),
(1087, 'Bella', 'Mendoza', 'bella.mendoza@email.com'),
(1088, 'Charles', 'Ruiz', 'charles.ruiz@email.com'),
(1089, 'Claire', 'Hughes', 'claire.hughes@email.com'),
(1090, 'Jaxon', 'Price', 'jaxon.price@email.com'),
(1091, 'Lucy', 'Alvarez', 'lucy.alvarez@email.com'),
(1092, 'Aaron', 'Castillo', 'aaron.castillo@email.com'),
(1093, 'Anna', 'Sanders', 'anna.sanders@email.com'),
(1094, 'Isaiah', 'Patel', 'isaiah.patel@email.com'),
(1095, 'Caroline', 'Myers', 'caroline.myers@email.com'),
(1096, 'Ezra', 'Long', 'ezra.long@email.com'),
(1097, 'Genesis', 'Ross', 'genesis.ross@email.com'),
(1098, 'Colton', 'Foster', 'colton.foster@email.com'),
(1099, 'Kennedy', 'Jimenez', 'kennedy.jimenez@email.com'),
(1100, 'Cameron', 'Powell', 'cameron.powell@email.com');
EOF

MYSQL_COUNT=$(docker exec mysql mysql -umysqluser -pmysqlpw -e "SELECT COUNT(*) FROM inventory.customers;" -s -N)
print_success "Inserted $MYSQL_COUNT customers into MySQL"

# Step 4: Register Debezium connector
print_step "Step 4: Registering Debezium MySQL connector..."
sleep 5  # Give Connect service a bit more time

curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" \
  localhost:8083/connectors/ -d '{
  "name": "inventory-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",
    "database.hostname": "mysql",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "dbz",
    "database.server.id": "184054",
    "topic.prefix": "dbserver1",
    "database.include.list": "inventory",
    "schema.history.internal.kafka.bootstrap.servers": "kafka:29092",
    "schema.history.internal.kafka.topic": "schemahistory.inventory"
  }
}' 2>&1 | grep -q "201 Created" && print_success "Connector registered" || print_error "Failed to register connector"

# Verify connector status
print_step "Verifying connector status..."
sleep 3
curl -s localhost:8083/connectors/inventory-connector/status | jq

echo
echo "========================================================================"
echo "  Setup Complete!"
echo "========================================================================"
echo
echo "Next steps:"
echo "  1. Activate Python environment:"
echo "     source cdc_env/bin/activate"
echo
echo "  2. Run the CDC consumer:"
echo "     python cdc.py              # Basic consumer"
echo "     python cdc_schema_evolution.py  # Schema-aware consumer"
echo
echo "  3. Test real-time changes:"
echo "     docker exec -it mysql mysql -umysqluser -pmysqlpw"
echo "     USE inventory;"
echo "     INSERT INTO customers VALUES (1101, 'Alice', 'Wonder', 'alice@email.com');"
echo
echo "  4. Follow the tutorial:"
echo "     cat TUTORIAL_SCHEMA_EVOLUTION.md"
echo
echo "========================================================================"
