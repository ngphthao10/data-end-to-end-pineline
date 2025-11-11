# Final Project Proposal: Real-Time E-Commerce Data Warehouse with CDC

## 📋 Executive Summary

This project implements an **end-to-end real-time data warehouse** for an e-commerce platform using **Change Data Capture (CDC)** technology. The system captures changes from operational databases in real-time, processes them through a streaming pipeline, and loads them into a dimensional data warehouse following **Kimball methodology** with proper Slowly Changing Dimension (SCD) handling.

**Key Value Proposition:**
- **Real-time Analytics**: Business intelligence updates within seconds instead of hours
- **Historical Tracking**: Complete audit trail for customer and product changes
- **Scalable Architecture**: Handles millions of transactions with Kafka and Flink
- **Production-Ready**: Fully containerized with monitoring and observability

---

## 🎯 Project Objectives

### Primary Goals
1. **Build a real-time data warehouse** for e-commerce analytics
2. **Implement SCD Type 1 & Type 2** patterns for dimension tables
3. **Design and load fact tables** with proper dimensional modeling
4. **Create an end-to-end CDC pipeline** using Debezium + Kafka
5. **Develop a monitoring dashboard** for pipeline health and data quality

### Learning Outcomes
- Master CDC concepts and implementation
- Understand dimensional modeling (star schema)
- Hands-on experience with streaming architectures
- Real-world SCD Type 1 & Type 2 implementation
- Data warehouse design and optimization

---

## 🏗️ Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    E-COMMERCE APPLICATION                        │
│  (Operational Database - PostgreSQL)                            │
│                                                                  │
│  Tables:                                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌─────────────┐      │
│  │customers │  │ products │  │ orders │  │ order_items │      │
│  └──────────┘  └──────────┘  └────────┘  └─────────────┘      │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        │ Debezium CDC Connector
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│                    APACHE KAFKA (Message Broker)                 │
│                                                                  │
│  Topics:                                                         │
│  • ecommerce.public.customers                                    │
│  • ecommerce.public.products                                     │
│  • ecommerce.public.orders                                       │
│  • ecommerce.public.order_items                                  │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        │ Kafka Consumer
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│              STREAM PROCESSING LAYER (Python/Flink)              │
│                                                                  │
│  • CDC Event Parser                                              │
│  • SCD Type 1 & Type 2 Logic                                     │
│  • Dimension Lookup & Surrogate Key Generation                   │
│  • Fact Table Construction                                       │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        │ Incremental Load
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│            DATA WAREHOUSE (PostgreSQL - Target)                  │
│                                                                  │
│  Star Schema:                                                    │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │dim_customer │   │dim_product  │   │  dim_date   │           │
│  │ (SCD Type 2)│   │ (SCD Type 2)│   │ (SCD Type 1)│           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                     │
│                     ┌──────▼──────┐                              │
│                     │ fact_orders │                              │
│                     │             │                              │
│                     │ • order_id  │                              │
│                     │ • customer_key (FK)                        │
│                     │ • product_key (FK)                         │
│                     │ • date_key (FK)                            │
│                     │ • quantity                                 │
│                     │ • unit_price                               │
│                     │ • total_amount                             │
│                     └─────────────┘                              │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│              ANALYTICS & VISUALIZATION LAYER                     │
│                                                                  │
│  • Flask REST API (Business Metrics)                             │
│  • React Dashboard (Real-time Monitoring)                        │
│  • Jupyter Notebooks (Ad-hoc Analysis)                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Infrastructure & Orchestration
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Containerization** | Docker, Docker Compose | Consistent development and deployment environment |
| **Source Database** | PostgreSQL 15 | E-commerce operational database |
| **Target Warehouse** | PostgreSQL 15 | Dimensional data warehouse |
| **Message Broker** | Apache Kafka 3.0 | Event streaming platform |
| **CDC Engine** | Debezium 3.0 | Change Data Capture connector |
| **Stream Processing** | Apache Flink 1.18 (Optional) | Real-time stream processing |

### Application Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| **ETL Logic** | Python 3.9+ | SCD processing, dimension loading |
| **Data Manipulation** | Pandas, SQLAlchemy | Efficient data transformation |
| **Backend API** | Flask 3.0 | REST endpoints for metrics |
| **Frontend** | React (Optional) | Real-time monitoring dashboard |
| **Notebooks** | Jupyter | Interactive analysis and demos |

### Data Quality & Monitoring
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Logging** | Python logging | Application logs |
| **Metrics** | Custom Python | Pipeline health checks |
| **Visualization** | Matplotlib, Seaborn | Data quality reports |

---

## 📊 Data Model Design

### Source Schema (Operational Database)

```sql
-- E-commerce OLTP Schema

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(500),
    city VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,  -- pending, processing, shipped, delivered
    total_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Target Schema (Data Warehouse - Star Schema)

```sql
-- Dimension Tables

-- SCD Type 2: Customer Dimension (tracks all changes)
CREATE TABLE dim_customer (
    customer_key SERIAL PRIMARY KEY,              -- Surrogate key
    customer_id INTEGER NOT NULL,                  -- Natural key
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    address VARCHAR(500),
    city VARCHAR(100),
    country VARCHAR(100),
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP DEFAULT '9999-12-31'::TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1
);

-- SCD Type 2: Product Dimension (tracks price changes)
CREATE TABLE dim_product (
    product_key SERIAL PRIMARY KEY,               -- Surrogate key
    product_id INTEGER NOT NULL,                   -- Natural key
    product_name VARCHAR(255),
    category VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    margin_percentage DECIMAL(5,2),                -- Derived field
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP DEFAULT '9999-12-31'::TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1
);

-- SCD Type 1: Date Dimension (static/slowly changing)
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,                  -- Format: YYYYMMDD
    date DATE NOT NULL,
    day_of_week VARCHAR(10),
    day_of_month INTEGER,
    month INTEGER,
    month_name VARCHAR(10),
    quarter INTEGER,
    year INTEGER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);

-- Fact Table
CREATE TABLE fact_orders (
    order_fact_key SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,                     -- Natural key from source
    order_item_id INTEGER NOT NULL,
    customer_key INTEGER REFERENCES dim_customer(customer_key),
    product_key INTEGER REFERENCES dim_product(product_key),
    date_key INTEGER REFERENCES dim_date(date_key),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    order_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_dim_customer_id ON dim_customer(customer_id, is_current);
CREATE INDEX idx_dim_product_id ON dim_product(product_id, is_current);
CREATE INDEX idx_fact_customer ON fact_orders(customer_key);
CREATE INDEX idx_fact_product ON fact_orders(product_key);
CREATE INDEX idx_fact_date ON fact_orders(date_key);
```

---

## 🔄 Implementation Phases

### Phase 1: Infrastructure Setup (Week 1)
**Deliverables:**
- [x] Docker Compose configuration for all services
- [x] PostgreSQL source database with sample e-commerce data
- [x] PostgreSQL target warehouse with star schema
- [x] Kafka + Zookeeper setup
- [x] Debezium connector configuration

**Tasks:**
1. Create source database with e-commerce schema
2. Generate realistic test data (1000+ customers, 500+ products, 5000+ orders)
3. Set up Kafka topics for each source table
4. Configure Debezium CDC connectors
5. Validate CDC events are flowing to Kafka

**Success Criteria:**
- All containers running and healthy
- CDC events visible in Kafka topics
- Can consume events from Python

---

### Phase 2: Dimension Table Loading (Week 2)
**Deliverables:**
- [x] SCD Type 1 implementation (dim_date)
- [x] SCD Type 2 implementation (dim_customer, dim_product)
- [x] Automated dimension loading pipeline
- [x] Jupyter notebook demonstrating SCD behavior

**Tasks:**
1. Implement dim_date loader (static/Type 1)
2. Implement SCD Type 2 logic for dim_customer
   - Detect changes (compare source vs current version)
   - End-date existing records
   - Insert new versions with incremented version number
3. Implement SCD Type 2 logic for dim_product
4. Create comprehensive tests for edge cases
5. Document SCD behavior with visual examples

**Success Criteria:**
- Customer address changes create new versions
- Product price changes create new versions
- Historical queries return correct point-in-time data
- Surrogate keys generated consistently

---

### Phase 3: Fact Table Loading (Week 3)
**Deliverables:**
- [x] Fact table loader with dimension lookups
- [x] Incremental load logic
- [x] Surrogate key resolution
- [x] Data quality checks

**Tasks:**
1. Implement dimension lookup logic
   - Find current customer_key for customer_id
   - Find current product_key for product_id at order time
   - Calculate date_key from order timestamp
2. Build fact_orders loader
   - Parse order_items CDC events
   - Resolve all foreign keys
   - Calculate derived metrics
3. Handle late-arriving facts
4. Implement idempotency (prevent duplicates)

**Success Criteria:**
- New orders automatically appear in fact table
- All foreign keys resolve correctly
- Can answer: "What was the product price when order X was placed?"
- No orphaned facts (all FKs valid)

---

### Phase 4: End-to-End Pipeline Integration (Week 4)
**Deliverables:**
- [x] Orchestrated pipeline (sequential dimension → fact loading)
- [x] Error handling and retry logic
- [x] Monitoring and alerting
- [x] Performance optimization

**Tasks:**
1. Create main pipeline orchestrator
2. Implement error handling for:
   - Kafka connection failures
   - Database deadlocks
   - Invalid data
3. Add logging and metrics collection
4. Optimize bulk inserts and updates
5. Create pipeline health dashboard

**Success Criteria:**
- Pipeline runs continuously without crashes
- Failed events are retried appropriately
- Processing latency < 5 seconds for simple events
- Dashboard shows pipeline metrics in real-time

---

### Phase 5: Business Scenarios & Demos (Week 5)
**Deliverables:**
- [x] Interactive Jupyter notebooks
- [x] Business scenario demonstrations
- [x] Flask API for metrics
- [x] Visualization dashboard (optional)

**Scenarios to Demonstrate:**

#### Scenario 1: Customer Address Change (SCD Type 2)
```
1. Customer moves to new address
2. CDC captures UPDATE event
3. Dim_customer: end-date old version, insert new version
4. Future orders use new customer_key
5. Historical orders still reference old customer_key
6. Query: "Where did customer X live when order Y was placed?"
```

#### Scenario 2: Product Price Increase (SCD Type 2)
```
1. Product price changes from $100 → $120
2. CDC captures UPDATE event
3. Dim_product: create new version with new price
4. Orders before change show $100, orders after show $120
5. Query: "What was the average product price in Q1 vs Q2?"
```

#### Scenario 3: New Order Placement (Fact Loading)
```
1. Customer places order with 3 items
2. CDC captures 3 INSERT events (order_items)
3. Pipeline resolves:
   - customer_key (current version at order time)
   - product_key (current version at order time)
   - date_key (from order timestamp)
4. 3 rows inserted into fact_orders
5. Query: "What was total revenue today?"
```

---

## 📈 Business Metrics & Analytics

### Key Performance Indicators (KPIs)

The data warehouse will enable these business queries:

#### Sales Analytics
```sql
-- Daily revenue trend
SELECT
    d.date,
    SUM(f.line_total) as daily_revenue,
    COUNT(DISTINCT f.order_id) as num_orders
FROM fact_orders f
JOIN dim_date d ON f.date_key = d.date_key
WHERE d.year = 2025 AND d.month = 11
GROUP BY d.date
ORDER BY d.date;

-- Top selling products
SELECT
    p.product_name,
    p.category,
    SUM(f.quantity) as units_sold,
    SUM(f.line_total) as revenue
FROM fact_orders f
JOIN dim_product p ON f.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;
```

#### Customer Analytics
```sql
-- Customer lifetime value
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name as customer_name,
    COUNT(DISTINCT f.order_id) as total_orders,
    SUM(f.line_total) as lifetime_value
FROM fact_orders f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.customer_id, customer_name
ORDER BY lifetime_value DESC;

-- Customer segmentation
SELECT
    c.city,
    c.country,
    COUNT(DISTINCT c.customer_id) as num_customers,
    SUM(f.line_total) as total_revenue
FROM fact_orders f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.city, c.country
ORDER BY total_revenue DESC;
```

#### Historical Analysis (SCD Type 2 Power)
```sql
-- Point-in-time pricing analysis
SELECT
    p.product_name,
    p.price as price_at_order_time,
    f.unit_price,
    f.quantity,
    d.date
FROM fact_orders f
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_date d ON f.date_key = d.date_key
WHERE p.product_id = 100
  AND d.date BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY d.date;
```

---

## 🧪 Testing Strategy

### Unit Tests
- SCD Type 1 logic (insert, update)
- SCD Type 2 logic (detect change, end-date, insert version)
- Dimension lookup functions
- Surrogate key generation

### Integration Tests
- End-to-end CDC flow (source → Kafka → warehouse)
- Multiple concurrent changes
- Late-arriving facts
- Out-of-order events

### Data Quality Tests
- Referential integrity (all FKs resolve)
- No duplicate facts
- SCD version consistency
- Surrogate key uniqueness

### Performance Tests
- Bulk load 10,000 orders
- Concurrent dimension updates
- Query performance on fact table (1M+ rows)

---

## 📊 Expected Outcomes

### Technical Achievements
1. **Functional real-time data warehouse** processing e-commerce events
2. **Production-quality SCD implementation** with comprehensive testing
3. **Scalable architecture** handling 1000s of events per second
4. **Monitoring and observability** with metrics and dashboards

### Deliverables
- [x] Full source code on GitHub with documentation
- [x] Docker Compose for one-command deployment
- [x] Jupyter notebooks demonstrating SCD behavior
- [x] REST API for querying business metrics
- [x] Final presentation with live demo

### Knowledge Gained
- Deep understanding of CDC patterns
- Hands-on dimensional modeling experience
- Real-world SCD Type 1 & 2 implementation
- Streaming architecture design
- Data warehouse performance optimization

---

## 🚀 How to Run (For Reviewers)

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- 8GB+ RAM

### Quick Start
```bash
# 1. Clone repository
git clone <repo-url>
cd cdc_kafka

# 2. Start all services
docker-compose up -d

# 3. Setup source database
docker exec -i postgres psql -U postgres < source_schema.sql

# 4. Configure CDC
curl -X POST http://localhost:8083/connectors -H "Content-Type: application/json" -d @debezium-config.json

# 5. Run ETL pipeline
python3 etl_pipeline.py

# 6. View results
jupyter notebook notebooks/SCD_Demo.ipynb
```

### Demo Scenarios
```bash
# Scenario 1: Customer address change
python3 demos/scenario_customer_change.py

# Scenario 2: Product price change
python3 demos/scenario_product_change.py

# Scenario 3: Order placement
python3 demos/scenario_order_placement.py
```

---

## 📅 Timeline & Milestones

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Infrastructure | All containers running, CDC flowing |
| 2 | Dimensions | SCD Type 1 & 2 working, tested |
| 3 | Facts | Fact loading with FK resolution |
| 4 | Integration | End-to-end pipeline orchestrated |
| 5 | Polish | Demos, documentation, presentation |

---

## 🎓 References & Resources

### Documentation
- [Debezium Documentation](https://debezium.io/documentation/)
- [Kimball Dimensional Modeling](https://www.kimballgroup.com/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)

### Code Repository Structure
```
cdc_kafka/
├── docker-compose.yml
├── source_schema.sql
├── warehouse_schema.sql
├── debezium-config.json
├── etl_pipeline.py
├── scd_implementation.py
├── scd_demo.py
├── notebooks/
│   └── SCD_Demo.ipynb
├── demos/
│   ├── scenario_customer_change.py
│   ├── scenario_product_change.py
│   └── scenario_order_placement.py
└── README.md
```
