# CDC (Change Data Capture) Demo with Debezium, Kafka, MySQL & PostgreSQL

Complete CDC system với Web Dashboard và Data Generator.

## Tính năng

- ✅ Real-time CDC replication (MySQL → PostgreSQL)
- ✅ Web Dashboard (Flask + Next.js + Tailwind CSS)
- ✅ Data Stream Generator (Apache Flink-style)
- ✅ Python CDC Consumer với schema evolution support
- ✅ Docker Compose setup (1 command)
- ✅ 100 realistic sample customers

## Kiến trúc

```
MySQL ──→ Debezium ──→ Kafka ──→ Python CDC Consumer ──→ PostgreSQL
   ↑                      ↓                                  ↓
   │                 Web Dashboard                      Flink Generator
   └──────────────────────┴────────────────────────────────────┘
                    Real-time CDC Pipeline
```

## Quick Start

### 1. Start tất cả services

```bash
docker-compose up -d
```

### 2. Setup database và connector

```bash
./setup_realistic_data.sh
```

### 3. Run CDC consumer

```bash
source cdc_env/bin/activate
python cdc_schema_evolution.py
```

### 4. Launch Web Dashboard

```bash
./start_dashboard.sh
```

Mở browser: **http://localhost:3000**

### 5. Generate data stream (optional)

```bash
./start_data_generator.sh
```

## Hướng dẫn chi tiết

Xem **[TUTORIAL.md](TUTORIAL.md)** để có hướng dẫn từng bước đầy đủ.

## Project Structure

```
cdc_kafka/
├── docker-compose.yml              # All services (Kafka, MySQL, PostgreSQL, Flink)
├── cdc_schema_evolution.py         # Python CDC consumer
├── flink_simple_generator.py       # Data stream generator
├── setup_realistic_data.sh         # Automated setup script
├── start_dashboard.sh              # Start web dashboard
├── start_data_generator.sh         # Start data generator
│
├── backend/                        # Flask API
│   ├── app.py
│   └── requirements.txt
│
├── frontend/                       # Next.js + Tailwind CSS
│   ├── app/
│   │   └── page.tsx               # Main dashboard
│   ├── package.json
│   └── tailwind.config.js
│
├── TUTORIAL.md                     # 📖 Complete step-by-step guide
└── README.md                       # This file
```

## Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| MySQL | 3306 | Source database |
| PostgreSQL | 5432 | Target database |
| Kafka | 9092 | Event streaming |
| Debezium Connect | 8083 | CDC connector |
| Flask Backend | 5000 | REST API |
| Next.js Frontend | 3000 | Web Dashboard |
| Flink JobManager | 8081 | Flink Web UI |

## Tech Stack

**Backend:**
- Debezium MySQL Connector
- Apache Kafka
- Flask REST API
- Python CDC Consumer
- SQLAlchemy

**Frontend:**
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Axios

**Data Generation:**
- Apache Flink (optional)
- Python Faker library

## Quick Commands

```bash
# Check connector status
curl -s localhost:8083/connectors/inventory-connector/status | jq

# Monitor Kafka CDC events
docker exec kafka /kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:29092 \
  --topic dbserver1.inventory.customers \
  --from-beginning

# MySQL console
docker exec -it mysql mysql -umysqluser -pmysqlpw

# PostgreSQL console
docker exec -it postgres psql -U postgres

# Check record counts
docker exec mysql mysql -umysqluser -pmysqlpw -e "SELECT COUNT(*) FROM inventory.customers;"
docker exec postgres psql -U postgres -c "SELECT COUNT(*) FROM customers;"

# Stop all services
docker-compose down
```

## Troubleshooting

Xem phần **Troubleshooting** trong [TUTORIAL.md](TUTORIAL.md)

Các vấn đề thường gặp:
- Port conflicts (PostgreSQL 5432)
- Kafka connection issues
- Connector not running
- Python dependencies

## Use Cases

- **Data Migration**: MySQL → PostgreSQL with zero downtime
- **Real-time Replication**: Keep databases in sync
- **Event-Driven Architecture**: React to DB changes
- **Audit Trail**: Track all data changes
- **Analytics Pipeline**: Stream data to data warehouse

## Next Steps

- Thêm authentication cho dashboard
- WebSocket support cho real-time updates
- Multi-table CDC replication
- Monitoring với Prometheus + Grafana
- Deploy lên Kubernetes

## Resources

- [Complete Tutorial](TUTORIAL.md) - Hướng dẫn từng bước đầy đủ
- [Debezium Documentation](https://debezium.io/documentation/)
- [Apache Kafka](https://kafka.apache.org/documentation/)
- [Next.js Documentation](https://nextjs.org/docs)

## License

MIT - Educational purposes

---

**📖 Bắt đầu với [TUTORIAL.md](TUTORIAL.md)**
