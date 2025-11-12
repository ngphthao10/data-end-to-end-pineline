# E-commerce Data Warehouse với CDC (Change Data Capture)

## Tổng Quan

Dự án này xây dựng một hệ thống Data Warehouse cho E-commerce, sử dụng CDC để đồng bộ dữ liệu thời gian thực từ database nguồn (source) sang data warehouse. Hệ thống theo dõi lịch sử thay đổi của khách hàng và sản phẩm theo chuẩn SCD Type 2.

## Kiến Trúc Hệ Thống

```
Source DB (PostgreSQL)
    ↓ [CDC - Debezium]
Kafka (Message Broker)
    ↓ [ETL Worker]
Warehouse DB (PostgreSQL)
    ↓ [Flask API]
Frontend Dashboard (Next.js)
```

## Cấu Trúc Thư Mục

```
cdc_kafka/
├── api/
│   └── app.py                    # Flask API - cung cấp REST endpoints
├── frontend/
│   ├── app/
│   │   ├── page.tsx              # Trang chủ - Dashboard
│   │   ├── analytics/            # Trang phân tích doanh thu
│   │   ├── cdc-monitoring/       # Theo dõi CDC sync
│   │   └── scd-history/          # Xem lịch sử thay đổi
│   ├── components/               # React components tái sử dụng
│   └── package.json
├── init_scripts/                 # SQL scripts khởi tạo database
├── db_config.py                  # Cấu hình kết nối database
├── etl_pipeline.py               # ETL Worker - xử lý Kafka messages
├── scd_processor.py              # Logic xử lý SCD Type 2
├── generate_data.py              # Script tạo dữ liệu mẫu
├── docker-compose.yml            # Cấu hình Docker services
├── Dockerfile.api                # Docker image cho API
├── Dockerfile.frontend           # Docker image cho Frontend
├── Dockerfile.etl                # Docker image cho ETL Worker
└── requirements.txt              # Python dependencies

```

## Các Thành Phần Chính

### 1. Source Database (PostgreSQL)
- **Port**: 5432
- **Database**: ecommerce_source
- Chứa dữ liệu operational:
  - `customers` - Thông tin khách hàng
  - `products` - Thông tin sản phẩm
  - `orders` - Đơn hàng
  - `order_items` - Chi tiết đơn hàng

### 2. Warehouse Database (PostgreSQL)
- **Port**: 5433
- **Database**: ecommerce_warehouse
- Chứa dữ liệu analytical theo mô hình Star Schema:
  - **Dimension Tables**:
    - `dim_customer` - Chiều khách hàng (SCD Type 2)
    - `dim_product` - Chiều sản phẩm (SCD Type 2)
    - `dim_date` - Chiều thời gian
  - **Fact Table**:
    - `fact_orders` - Bảng fact đơn hàng

### 3. Kafka + Debezium
- **Kafka Port**: 9092
- **Debezium Connect Port**: 8083
- Chức năng:
  - Debezium theo dõi thay đổi trên Source DB
  - Gửi events về Kafka topics
  - ETL Worker lắng nghe và xử lý

### 4. ETL Worker (Python)
- **File**: `etl_pipeline.py`
- Chức năng:
  - Consume messages từ Kafka
  - Xử lý SCD Type 2 cho customers và products
  - Load dữ liệu vào Warehouse
- **File liên quan**: `scd_processor.py`

### 5. API Backend (Flask)
- **Port**: 5000
- **File**: `api/app.py`
- Endpoints chính:
  - `/api/metrics/daily-revenue` - Doanh thu theo ngày
  - `/api/metrics/top-products` - Sản phẩm bán chạy
  - `/api/metrics/top-customers` - Khách hàng VIP
  - `/api/cdc/stats` - Thống kê CDC sync
  - `/api/customers/<id>/history` - Lịch sử khách hàng
  - `/api/products/<id>/history` - Lịch sử giá sản phẩm

### 6. Frontend Dashboard (Next.js)
- **Port**: 3000
- **Framework**: Next.js 14 + TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- Các trang:
  - **Dashboard**: Tổng quan metrics
  - **Analytics**: Phân tích doanh thu chi tiết
  - **CDC Monitoring**: Theo dõi đồng bộ dữ liệu
  - **SCD History**: Xem lịch sử thay đổi khách hàng/sản phẩm

## Công Nghệ Sử Dụng

### Backend
- **Python 3.9**
  - Flask (API framework)
  - SQLAlchemy (ORM)
  - kafka-python (Kafka client)
  - psycopg2 (PostgreSQL driver)

### Frontend
- **Node.js 18**
  - Next.js 14
  - React 18
  - TypeScript
  - Tailwind CSS
  - Recharts (charting library)
  - Axios (HTTP client)

### Infrastructure
- **Docker & Docker Compose**
- **PostgreSQL 15** (Source & Warehouse)
- **Apache Kafka** (Message Broker)
- **Debezium 3.0** (CDC Platform)

## Luồng Dữ Liệu

1. **Insert/Update** dữ liệu vào Source DB (customers, products, orders)
2. **Debezium** phát hiện thay đổi qua PostgreSQL WAL (Write-Ahead Log)
3. **Kafka** nhận CDC events từ Debezium
4. **ETL Worker** consume messages và:
   - Xử lý SCD Type 2 cho dimension tables
   - Insert vào fact table
5. **API** query dữ liệu từ Warehouse
6. **Frontend** hiển thị dashboard và analytics

## SCD Type 2 Implementation

**Slowly Changing Dimension Type 2** giữ toàn bộ lịch sử thay đổi:

### Ví dụ: Customer thay đổi địa chỉ

| customer_key | customer_id | name | address | valid_from | valid_to | is_current | version |
|--------------|-------------|------|---------|------------|----------|------------|---------|
| 1 | 101 | John | HN | 2024-01-01 | 2024-06-01 | FALSE | 1 |
| 2 | 101 | John | SG | 2024-06-01 | 9999-12-31 | TRUE | 2 |

- `valid_from/valid_to`: Thời gian record có hiệu lực
- `is_current`: TRUE cho bản ghi hiện tại
- `version`: Số thứ tự thay đổi

## Metrics & Analytics

Dashboard cung cấp:
- **Doanh thu theo ngày/tuần/tháng**
- **Top sản phẩm bán chạy**
- **Top khách hàng** (theo lifetime value)
- **Phân tích theo danh mục sản phẩm**
- **Trạng thái đồng bộ CDC**
- **Lịch sử thay đổi giá và thông tin khách hàng**

## Bắt Đầu

Xem file [TUTORIAL.md](./TUTORIAL.md) để biết cách chạy project.

## Lưu Ý

- Dữ liệu được lưu trong Docker volumes, không mất khi restart
- Frontend có hot reload, tự động cập nhật khi sửa code
- API và ETL cần restart container sau khi sửa code
- SCD Type 2 giữ toàn bộ lịch sử, không xóa dữ liệu cũ
- Debezium sử dụng PostgreSQL logical replication (wal_level=logical)
