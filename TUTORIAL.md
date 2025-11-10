# CDC (Change Data Capture) Tutorial với Debezium, Kafka, MySQL và PostgreSQL

Hướng dẫn từng bước để xây dựng hệ thống CDC hoàn chỉnh với Web Dashboard và Data Generator.

## Tổng quan

1. Prerequisites
2. Start Docker Compose services
3. Setup MySQL và PostgreSQL databases
4. Setup Debezium MySQL Connector
5. Setup Python CDC Consumer
6. Setup Web Dashboard (Flask + Next.js)
7. Setup Flink Data Generator
8. Testing và Demo
9. Troubleshooting
10. Clean up

## Kiến trúc hệ thống

```
┌──────────────┐
│    Flink      │
│ Data Generator│
│               │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌────────────┐      ┌───────────┐
│   MySQL      │─────▶│  Debezium  │─────▶│   Kafka   │
│  (Source)    │      │  Connector │      │  (Stream) │
└──────────────┘      └────────────┘      └─────┬─────┘
                                                 │
       ┌─────────────────────────────────────────┼─────────────┐
       │                                         │             │
       ▼                                         ▼             ▼
┌──────────────┐                        ┌──────────────┐   ┌──────────────┐
│ Python CDC   │                        │ PostgreSQL   │   │ Web Dashboard│
│  Consumer    │───────────────────────▶│   (Target)   │   │ (Monitor)    │
└──────────────┘                        └──────────────┘   └──────────────┘


```

---

## 1. Prerequisites

### Cài đặt cơ bản

- **Docker và Docker Compose**
  - Mac/Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Linux: [Docker](https://docs.docker.com/engine/install/) + [Docker Compose](https://docs.docker.com/compose/install/)

- **Python 3.9+**
  ```bash
  python3 --version
  ```

- **Node.js 18+** (cho Web Dashboard)
  ```bash
  node --version
  ```

- **jq** (optional - để format JSON)
  - Mac: `brew install jq`
  - Linux: `sudo apt install jq -y`

---

## 2. Start Docker Compose services

### Start tất cả services

```bash
docker-compose up -d
```

Services bao gồm:
- Zookeeper (port 2181)
- Kafka (port 9092, 29092)
- MySQL (port 3306)
- PostgreSQL (port 5432)
- Debezium Connect (port 8083)
- Flink JobManager (port 8081)
- Flink TaskManager

### Verify services đang chạy

```bash
docker-compose ps
```

Tất cả services phải có status **Up**.

### Check logs nếu cần

```bash
docker-compose logs kafka
docker-compose logs mysql
docker-compose logs postgres
docker-compose logs connect
```

---

## 3. Setup MySQL và PostgreSQL databases

### 3.1. MySQL - Create và populate data

**Connect vào MySQL:**

```bash
docker exec -it mysql mysql -umysqluser -pmysqlpw
```

**Create table:**

```sql
USE inventory;

DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Populate 100 realistic customers:**

```sql
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
(1025, 'Elizabeth', 'Sanchez', 'elizabeth.sanchez@email.com');

-- Thêm 75 customers nữa để đủ 100
INSERT INTO customers (id, first_name, last_name, email) VALUES
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
```

**Verify data:**

```sql
SELECT COUNT(*) FROM customers;  -- Should return 100
SELECT * FROM customers LIMIT 5;
```

Exit với `exit` hoặc `Ctrl+D`.

### 3.2. PostgreSQL - Create target table

**Connect vào PostgreSQL:**

```bash
docker exec -it postgres psql -U postgres
```

**Create table:**

```sql
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\d customers
```

Exit với `\q` hoặc `Ctrl+D`.

---

## 4. Setup Debezium MySQL Connector

### Check Debezium Connect service

```bash
curl -H "Accept:application/json" localhost:8083/
```

### List connectors (should be empty)

```bash
curl -H "Accept:application/json" localhost:8083/connectors/
```

### Register MySQL connector

```bash
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
}'
```

Should return **201 Created**.

### Verify connector status

```bash
curl -s localhost:8083/connectors/inventory-connector/status | jq
```

Status phải là **RUNNING**.

### Monitor Kafka CDC events

```bash
docker exec kafka /kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:29092 \
  --topic dbserver1.inventory.customers \
  --from-beginning | jq '.payload | {op, before, after}'
```

Bạn sẽ thấy 100 snapshot records với `"op": "r"`.

Press `Ctrl+C` để thoát.

---

## 5. Setup Python CDC Consumer

### 5.1. Create Python virtual environment

```bash
python3 -m venv cdc_env
source cdc_env/bin/activate
```

### 5.2. Install dependencies

```bash
pip install --upgrade pip
pip install kafka-python sqlalchemy psycopg2-binary pymysql
```

### 5.3. Run CDC consumer

File `cdc_schema_evolution.py` đã có sẵn trong project.

```bash
python cdc_schema_evolution.py
```

**Output:**

```
Starting CDC consumer...
Listening for changes on MySQL customers table...
✓ SNAPSHOT: Emma Johnson
✓ SNAPSHOT: Liam Williams
...
(100 records processed)
```

CDC consumer sẽ:
- Process initial snapshot (100 customers)
- Replicate vào PostgreSQL
- Listen cho real-time changes

Để chạy ở background:

```bash
python cdc_schema_evolution.py &
```

### 5.4. Verify PostgreSQL data

```bash
docker exec -i postgres psql -U postgres << 'EOF'
SELECT COUNT(*) FROM customers;
SELECT * FROM customers ORDER BY id LIMIT 5;
EOF
```

Should see 100 customers.

---

## 6. Setup Web Dashboard

Dashboard cung cấp:
- Real-time CDC event monitoring
- Side-by-side MySQL ↔ PostgreSQL comparison
- CRUD operations (Create, Read, Update, Delete)
- Statistics và connector status

### 6.1. Setup Flask Backend

**Open new terminal:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Run Flask server:**

```bash
python app.py
```

Backend sẽ chạy ở **http://localhost:5000**

### 6.2. Setup Next.js Frontend

**Open another new terminal:**

```bash
cd frontend
npm install
npm run dev
```

Frontend sẽ chạy ở **http://localhost:3000**

### 6.3. Access Web Dashboard

Mở browser: **http://localhost:3000**

Dashboard hiển thị:
- **Statistics Cards**: MySQL records, PostgreSQL records, Sync status, Connector status
- **Database Comparison**: Side-by-side tables
- **CDC Events Stream**: Real-time event feed với icons
- **CRUD Operations**: Add, Edit, Delete buttons

---

## 7. Setup Flink Data Generator

Flink Data Generator tạo continuous stream of INSERT/UPDATE/DELETE operations để test CDC pipeline.

### 7.1. Install dependencies

```bash
# Activate Python environment (nếu chưa)
source cdc_env/bin/activate

# Install Faker and PyMySQL
pip install faker pymysql
```

### 7.2. Run Data Generator

```bash
python flink_simple_generator.py
```

**Output:**

```
🚀 Starting Flink-style Data Stream Generator
📊 This simulates Apache Flink DataStream operations

✓ Connected to MySQL

[14:23:15.234] ✓ ➕ INSERT | INSERT id=2001, Sarah Johnson
[14:23:15.734] ✓ ✏️  UPDATE | UPDATE id=1023, first_name=Michael
[14:23:16.234] ✓ 🗑️  DELETE | DELETE id=1089

----------------------------------------------------------------------
  Statistics | Total Operations: 20 | Customers: 118
  INSERT:   10 | UPDATE:    6 | DELETE:    4
----------------------------------------------------------------------
```

Generator sẽ:
- Tạo 2 operations/second (configurable)
- Distribution: INSERT 50%, UPDATE 30%, DELETE 20%
- Hiển thị real-time statistics

Hoặc dùng script tự động:

```bash
./start_data_generator.sh
```

### 7.3. Adjust Configuration

Edit `flink_simple_generator.py` line 185-188:

```python
RATE_PER_SECOND = 2      # Tốc độ (operations/giây)
INSERT_RATIO = 0.5       # 50% inserts
UPDATE_RATIO = 0.3       # 30% updates
DELETE_RATIO = 0.2       # 20% deletes
```

---

## 8. Testing và Demo

### Full System Test

Mở 4 terminals:

**Terminal 1 - CDC Consumer:**

```bash
source cdc_env/bin/activate
python cdc_schema_evolution.py
```

**Terminal 2 - Data Generator:**

```bash
source cdc_env/bin/activate
python flink_simple_generator.py
```

**Terminal 3 - Monitor Kafka:**

```bash
docker exec kafka /kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:29092 \
  --topic dbserver1.inventory.customers \
  --from-beginning
```

**Terminal 4 - Watch PostgreSQL:**

```bash
watch -n 2 'docker exec -i postgres psql -U postgres -c "SELECT COUNT(*) FROM customers;"'
```

**Browser - Web Dashboard:**

Open: **http://localhost:3000**

### Test Scenarios

#### Test 1: Manual INSERT via MySQL

```bash
docker exec -i mysql mysql -umysqluser -pmysqlpw << 'EOF'
USE inventory;
INSERT INTO customers (id, first_name, last_name, email)
VALUES (2050, 'Alice', 'Wonder', 'alice@example.com');
EOF
```

**Watch:**
- Terminal 1: CDC consumer processes the INSERT
- Terminal 3: Kafka shows CDC event
- Terminal 4: PostgreSQL count increases
- Browser: New record appears in dashboard

#### Test 2: UPDATE via Web Dashboard

1. Go to http://localhost:3000
2. Click **Edit** icon (pencil) next to any customer
3. Change first name or email
4. Click **Update Customer**

**Watch:**
- CDC consumer shows UPDATE event
- Both MySQL and PostgreSQL tables updated
- CDC Events stream shows UPDATE badge

#### Test 3: DELETE via Web Dashboard

1. Click **Trash** icon next to a customer
2. Confirm deletion

**Watch:**
- Record disappears from both databases
- CDC Events stream shows DELETE event

#### Test 4: Continuous Data Generation

With Flink generator running, watch:
- Real-time INSERT/UPDATE/DELETE operations
- CDC events flowing through Kafka
- PostgreSQL automatically syncing
- Dashboard updating every 2 seconds
- Statistics counter increasing

#### Test 5: Schema Evolution

**Add new column to MySQL:**

```bash
docker exec -i mysql mysql -umysqluser -pmysqlpw << 'EOF'
USE inventory;
ALTER TABLE customers ADD COLUMN phone VARCHAR(20);
UPDATE customers SET phone='555-1234' WHERE id=1001;
EOF
```

**Add same column to PostgreSQL:**

```bash
docker exec -i postgres psql -U postgres << 'EOF'
ALTER TABLE customers ADD COLUMN phone VARCHAR(20);
EOF
```

**Insert new data with phone:**

```bash
docker exec -i mysql mysql -umysqluser -pmysqlpw << 'EOF'
USE inventory;
INSERT INTO customers (id, first_name, last_name, email, phone)
VALUES (2060, 'Bob', 'Builder', 'bob@example.com', '555-5678');
EOF
```

Watch CDC consumer handle new schema automatically!

---

## 9. Troubleshooting

### Docker services không start

```bash
# Stop all
docker-compose down

# Remove volumes
docker-compose down -v

# Start lại
docker-compose up -d

# Wait 15 seconds
sleep 15
```

### Kafka không có messages

**Check connector status:**

```bash
curl -s localhost:8083/connectors/inventory-connector/status | jq
```

Should see `"state": "RUNNING"`.

**Check Kafka topics:**

```bash
docker exec kafka /kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:29092 \
  --list
```

Should see `dbserver1.inventory.customers`.

### PostgreSQL connection error

**Check if local PostgreSQL is running:**

```bash
# Mac
brew services list | grep postgresql

# Stop local PostgreSQL if running
brew services stop postgresql@15
```

**Verify Docker PostgreSQL:**

```bash
docker exec -i postgres psql -U postgres -c "SELECT version();"
```

### Web Dashboard không load

**Check Flask backend:**

```bash
curl http://localhost:5000/api/health
```

Should return `{"status": "healthy"}`.

**Check Next.js:**

```bash
# In frontend directory
npm run dev
```

**CORS errors:**

Backend đã có Flask-CORS. Nếu vẫn lỗi:

```bash
cd backend
pip install flask-cors
```

### CDC Consumer lỗi import

```bash
pip uninstall kafka-python
pip install kafka-python==2.0.2
```

### Data Generator không connect

```bash
# Test MySQL connection
docker exec mysql mysql -umysqluser -pmysqlpw -e "SELECT 1;"

# Check network
docker network inspect cdc_kafka_cdc-network
```

---

## 10. Clean up

### Stop all processes

Press `Ctrl+C` trong từng terminal đang chạy:
- CDC Consumer
- Data Generator
- Flask backend
- Next.js frontend

### Stop Docker services

```bash
docker-compose down
```

### Remove volumes (xóa hết data)

```bash
docker-compose down -v
```

### Deactivate Python environment

```bash
deactivate
```

---

## Automated Setup Script

Để setup tự động, dùng script có sẵn:

```bash
./setup_realistic_data.sh
```

Script này sẽ:
1. Start Docker Compose services
2. Create PostgreSQL table
3. Populate MySQL với 100 customers
4. Register Debezium connector
5. Verify connector status

Sau đó chỉ cần:

```bash
# Terminal 1: CDC Consumer
source cdc_env/bin/activate
python cdc_schema_evolution.py

# Terminal 2: Web Dashboard
./start_dashboard.sh

# Terminal 3: Data Generator (optional)
./start_data_generator.sh
```

---

## Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Check connector
curl -s localhost:8083/connectors/inventory-connector/status | jq

# MySQL console
docker exec -it mysql mysql -umysqluser -pmysqlpw

# PostgreSQL console
docker exec -it postgres psql -U postgres

# Monitor Kafka
docker exec kafka /kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:29092 \
  --topic dbserver1.inventory.customers \
  --from-beginning

# Check counts
docker exec mysql mysql -umysqluser -pmysqlpw -e "SELECT COUNT(*) FROM inventory.customers;"
docker exec postgres psql -U postgres -c "SELECT COUNT(*) FROM customers;"

# Restart connector
curl -X POST localhost:8083/connectors/inventory-connector/restart

# Delete connector
curl -X DELETE localhost:8083/connectors/inventory-connector

# Stop all
docker-compose down
```

---

## Tài liệu tham khảo

- [Debezium Documentation](https://debezium.io/documentation/)
- [Apache Kafka](https://kafka.apache.org/documentation/)
- [Apache Flink](https://flink.apache.org/docs/stable/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## Tổng kết

Bạn đã học cách:
- ✓ Setup CDC pipeline với Debezium + Kafka
- ✓ Replicate data từ MySQL sang PostgreSQL real-time
- ✓ Build Python CDC consumer
- ✓ Create Web Dashboard với Flask + Next.js
- ✓ Generate continuous data stream với Flink
- ✓ Monitor và test CDC operations
- ✓ Handle schema evolution

**Next Steps:**
- Thêm authentication cho dashboard
- WebSocket support cho real-time updates
- Multi-table CDC replication
- Deploy lên production (Kubernetes)
- Add monitoring với Prometheus + Grafana

Chúc bạn thành công! 🚀
