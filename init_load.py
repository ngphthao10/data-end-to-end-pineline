"""Initial load script để load data từ source vào warehouse"""
import logging
from db_config import get_source_engine, get_warehouse_engine
from scd_processor import SCDProcessor
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_load():
    """Load initial data from source to warehouse"""
    source_engine = get_source_engine()
    warehouse_engine = get_warehouse_engine()
    scd_processor = SCDProcessor(warehouse_engine)

    logger.info("Starting initial data load...")

    # Populate dim_date table first
    logger.info("Populating dim_date table...")
    from datetime import datetime, timedelta
    with warehouse_engine.connect() as conn:
        # Check if dim_date already populated
        count = conn.execute(text("SELECT COUNT(*) FROM dim_date")).scalar()
        if count == 0:
            # Generate dates from 2020-01-01 to 2030-12-31
            start_date = datetime(2020, 1, 1)
            end_date = datetime(2030, 12, 31)
            current_date = start_date

            dates_to_insert = []
            while current_date <= end_date:
                date_key = int(current_date.strftime('%Y%m%d'))
                dates_to_insert.append({
                    'date_key': date_key,
                    'date': current_date.date(),
                    'day_of_week': current_date.strftime('%A'),
                    'day_of_month': current_date.day,
                    'month': current_date.month,
                    'month_name': current_date.strftime('%B'),
                    'quarter': (current_date.month - 1) // 3 + 1,
                    'year': current_date.year,
                    'is_weekend': current_date.weekday() >= 5,
                    'is_holiday': False
                })
                current_date += timedelta(days=1)

            # Bulk insert
            for batch_start in range(0, len(dates_to_insert), 1000):
                batch = dates_to_insert[batch_start:batch_start + 1000]
                conn.execute(
                    text("""INSERT INTO dim_date (date_key, date, day_of_week, day_of_month, month, month_name, quarter, year, is_weekend, is_holiday)
                            VALUES (:date_key, :date, :day_of_week, :day_of_month, :month, :month_name, :quarter, :year, :is_weekend, :is_holiday)"""),
                    batch
                )
                conn.commit()
            logger.info(f"  Inserted {len(dates_to_insert)} dates")
        else:
            logger.info(f"  dim_date already has {count} records, skipping")

    logger.info("✓ dim_date populated")

    # Load customers
    logger.info("Loading customers...")
    with source_engine.connect() as conn:
        customers = conn.execute(text("SELECT * FROM customers ORDER BY customer_id")).fetchall()
        for idx, customer in enumerate(customers):
            customer_data = {
                'customer_id': customer[0],
                'first_name': customer[1],
                'last_name': customer[2],
                'email': customer[3],
                'phone': customer[4],
                'address': customer[5],
                'city': customer[6],
                'country': customer[7]
            }
            scd_processor.process_customer_scd2(customer_data, 'c')
            if (idx + 1) % 100 == 0:
                logger.info(f"  Loaded {idx + 1}/{len(customers)} customers")

    logger.info(f"✓ Loaded {len(customers)} customers")

    # Load products
    logger.info("Loading products...")
    with source_engine.connect() as conn:
        products = conn.execute(text("SELECT * FROM products ORDER BY product_id")).fetchall()
        for idx, product in enumerate(products):
            product_data = {
                'product_id': product[0],
                'product_name': product[1],
                'category': product[2],
                'brand': product[3],
                'price': float(product[4]),
                'cost': float(product[5]),
                'description': product[6]
            }
            scd_processor.process_product_scd2(product_data, 'c')
            if (idx + 1) % 100 == 0:
                logger.info(f"  Loaded {idx + 1}/{len(products)} products")

    logger.info(f"✓ Loaded {len(products)} products")

    # Load order_items to fact table
    logger.info("Loading order items to fact table...")
    warehouse_engine = get_warehouse_engine()

    with source_engine.connect() as source_conn:
        order_items = source_conn.execute(text("""
            SELECT oi.order_item_id, oi.order_id, oi.product_id, oi.quantity,
                   oi.unit_price, oi.line_total, o.customer_id, o.order_date
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            ORDER BY oi.order_item_id
        """)).fetchall()

        loaded_count = 0
        for order_item in order_items:
            order_item_id, order_id, product_id, quantity, unit_price, line_total, customer_id, order_date = order_item

            with warehouse_engine.connect() as warehouse_conn:
                # Get customer key
                customer_key_result = warehouse_conn.execute(
                    text("""SELECT customer_key FROM dim_customer
                            WHERE customer_id = :customer_id AND is_current = TRUE"""),
                    {'customer_id': customer_id}
                ).fetchone()

                # Get product key
                product_key_result = warehouse_conn.execute(
                    text("""SELECT product_key FROM dim_product
                            WHERE product_id = :product_id AND is_current = TRUE"""),
                    {'product_id': product_id}
                ).fetchone()

                if not customer_key_result or not product_key_result:
                    continue

                customer_key = customer_key_result[0]
                product_key = product_key_result[0]

                # Get date key
                date_str = order_date.strftime('%Y%m%d')
                date_key = int(date_str)

                # Insert into fact table
                warehouse_conn.execute(
                    text("""
                        INSERT INTO fact_orders
                        (order_id, order_item_id, customer_key, product_key, date_key,
                         quantity, unit_price, line_total)
                        VALUES (:order_id, :order_item_id, :customer_key, :product_key, :date_key,
                                :quantity, :unit_price, :line_total)
                    """),
                    {
                        'order_id': order_id,
                        'order_item_id': order_item_id,
                        'customer_key': customer_key,
                        'product_key': product_key,
                        'date_key': date_key,
                        'quantity': quantity,
                        'unit_price': float(unit_price),
                        'line_total': float(line_total)
                    }
                )
                warehouse_conn.commit()

                loaded_count += 1
                if loaded_count % 500 == 0:
                    logger.info(f"  Loaded {loaded_count}/{len(order_items)} order items to fact table")

        logger.info(f"✓ Loaded {loaded_count} order items to fact table")

    logger.info("Initial data load completed!")

if __name__ == "__main__":
    init_load()
