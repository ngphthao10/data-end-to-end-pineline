# Hướng Dẫn Chạy Project

## Yêu Cầu
- Docker và Docker Compose đã cài đặt
- Có kết nối internet (lần đầu cần tải images)

## Các Bước Chạy

### 1. Khởi động toàn bộ hệ thống

```bash
docker-compose up -d
```

Lệnh này sẽ khởi động:
- Zookeeper và Kafka (message broker)
- 2 PostgreSQL databases (source và warehouse)
- Debezium Connect (CDC connector)
- ETL Worker (xử lý dữ liệu)
- Flask API (backend)
- Next.js Frontend (dashboard)

### 2. Kiểm tra các container đang chạy

```bash
docker-compose ps
```

Bạn sẽ thấy danh sách các container và trạng thái của chúng.

### 3. Truy cập ứng dụng

- **Frontend Dashboard**: http://localhost:3000
- **API Backend**: http://localhost:5000
- **Debezium Connect**: http://localhost:8083

### 4. Tạo dữ liệu mẫu

```bash
python generate_data.py
```

Script này sẽ tạo:
- Customers (khách hàng)
- Products (sản phẩm)
- Orders (đơn hàng)

### 5. Xem logs của các service

```bash
# Xem tất cả logs
docker-compose logs -f

# Xem logs của service cụ thể
docker-compose logs -f etl-worker
docker-compose logs -f api
docker-compose logs -f frontend
```

### 6. Dừng hệ thống

```bash
# Dừng nhưng giữ lại dữ liệu
docker-compose stop

# Dừng và xóa containers (giữ lại volumes)
docker-compose down

# Dừng và xóa hết (bao gồm cả database)
docker-compose down -v
```

## Các Lệnh Hữu Ích

### Build lại image khi sửa code

```bash
# Build lại API
docker-compose build api
docker-compose up -d api

# Build lại Frontend
docker-compose build frontend
docker-compose up -d frontend

# Build lại ETL Worker
docker-compose build etl-worker
docker-compose up -d etl-worker
```

### Restart một service

```bash
docker-compose restart api
docker-compose restart frontend
docker-compose restart etl-worker
```

### Kiểm tra database

```bash
# Vào PostgreSQL source
docker exec -it postgres-source psql -U postgres -d ecommerce_source

# Vào PostgreSQL warehouse
docker exec -it postgres-warehouse psql -U postgres -d ecommerce_warehouse

# Trong psql, dùng các lệnh:
\dt              # Xem danh sách tables
\d table_name    # Xem cấu trúc table
SELECT * FROM customers LIMIT 10;
\q               # Thoát
```

## Xử Lý Lỗi

### Container không chạy được
```bash
# Xem logs để tìm lỗi
docker-compose logs [service_name]

# Restart service
docker-compose restart [service_name]
```

### Port đã được sử dụng
- Kiểm tra các port: 3000, 5000, 5432, 5433, 8083, 9092
- Tắt các ứng dụng đang dùng port đó
- Hoặc sửa port trong `docker-compose.yml`

### Xóa dữ liệu và bắt đầu lại
```bash
docker-compose down -v
docker-compose up -d
```

## Tips

- Frontend có hot reload: sửa code frontend sẽ tự động cập nhật
- API có volume mount: sửa code API cần restart container
- ETL worker chạy liên tục, theo dõi Kafka messages
- Dữ liệu trong database được lưu trong Docker volumes, không mất khi restart


chỉ định worker node

tracking được record process lỗi


role, ngữ cảnh msk

kafka principle :chi phí, bảo mật

![alt text](image.png)

## Sơ đồ luồng xử lý tổng quát trong hệ thống