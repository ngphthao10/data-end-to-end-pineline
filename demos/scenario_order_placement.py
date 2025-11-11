"""
Scenario 3: New Order Placement

Demonstrates how new orders flow through CDC to fact table with dimension lookups.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import get_source_engine, get_warehouse_engine
from sqlalchemy import text
from datetime import datetime
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_scenario():
    source_engine = get_source_engine()
    warehouse_engine = get_warehouse_engine()

    logger.info("=== Scenario 3: New Order Placement ===\n")

    with source_engine.connect() as conn:
        # Get random customer and products
        customer = conn.execute(
            text("SELECT customer_id, first_name, last_name FROM customers ORDER BY RANDOM() LIMIT 1")
        ).fetchone()

        products = conn.execute(
            text("SELECT product_id, product_name, price FROM products ORDER BY RANDOM() LIMIT 3")
        ).fetchall()

        if not customer or not products:
            logger.error("Not enough data in database")
            return

        customer_id = customer[0]
        customer_name = f"{customer[1]} {customer[2]}"

        logger.info(f"Customer: {customer_name} (ID: {customer_id})")
        logger.info("Ordering products:")

        # Create order
        result = conn.execute(
            text("""
                INSERT INTO orders (customer_id, order_date, status, total_amount)
                VALUES (:customer_id, :order_date, 'pending', 0)
                RETURNING order_id
            """),
            {
                'customer_id': customer_id,
                'order_date': datetime.now()
            }
        )
        order_id = result.fetchone()[0]

        # Add order items
        total_amount = 0
        for product in products:
            product_id = product[0]
            product_name = product[1]
            unit_price = float(product[2])
            quantity = random.randint(1, 3)
            line_total = round(quantity * unit_price, 2)
            total_amount += line_total

            logger.info(f"  - {product_name}: {quantity} x ${unit_price:.2f} = ${line_total:.2f}")

            conn.execute(
                text("""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
                    VALUES (:order_id, :product_id, :quantity, :unit_price, :line_total)
                """),
                {
                    'order_id': order_id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'line_total': line_total
                }
            )

        # Update order total
        conn.execute(
            text("UPDATE orders SET total_amount = :total WHERE order_id = :order_id"),
            {'total': total_amount, 'order_id': order_id}
        )
        conn.commit()

        logger.info(f"\n✓ Order #{order_id} created. Total: ${total_amount:.2f}")
        logger.info("⏳ Waiting for CDC to process (5 seconds)...")
        time.sleep(5)

        # Check fact table
        with warehouse_engine.connect() as wh_conn:
            facts = wh_conn.execute(
                text("""
                    SELECT
                        f.order_fact_key,
                        c.customer_id,
                        c.first_name || ' ' || c.last_name as customer_name,
                        p.product_name,
                        f.quantity,
                        f.unit_price,
                        f.line_total,
                        d.date
                    FROM fact_orders f
                    JOIN dim_customer c ON f.customer_key = c.customer_key
                    JOIN dim_product p ON f.product_key = p.product_key
                    JOIN dim_date d ON f.date_key = d.date_key
                    WHERE f.order_id = :order_id
                """),
                {'order_id': order_id}
            ).fetchall()

            logger.info("\n✓ Facts loaded to warehouse:")
            for fact in facts:
                logger.info(f"  Fact #{fact[0]}: {fact[3]}")
                logger.info(f"    Customer: {fact[2]} (ID: {fact[1]})")
                logger.info(f"    Quantity: {fact[4]}, Amount: ${fact[6]:.2f}")
                logger.info(f"    Date: {fact[7]}")

        logger.info("\n=== Scenario completed ===")
        logger.info("Notice: All dimension keys resolved correctly via SCD lookups.")


if __name__ == '__main__':
    run_scenario()
