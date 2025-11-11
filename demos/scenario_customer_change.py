"""
Scenario 1: Customer Address Change (SCD Type 2)

Demonstrates how SCD Type 2 tracks customer address changes over time.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import get_source_engine, get_warehouse_engine
from sqlalchemy import text
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_scenario():
    source_engine = get_source_engine()
    warehouse_engine = get_warehouse_engine()

    logger.info("=== Scenario 1: Customer Address Change ===\n")

    with source_engine.connect() as conn:
        # Get a random customer
        result = conn.execute(
            text("SELECT customer_id, first_name, last_name, address, city FROM customers LIMIT 1")
        ).fetchone()

        if not result:
            logger.error("No customers found in database")
            return

        customer_id = result[0]
        name = f"{result[1]} {result[2]}"
        old_address = result[3]
        old_city = result[4]

        logger.info(f"Customer: {name} (ID: {customer_id})")
        logger.info(f"Current Address: {old_address}, {old_city}\n")

        # Check current version in warehouse
        with warehouse_engine.connect() as wh_conn:
            versions = wh_conn.execute(
                text("""
                    SELECT version, address, city, valid_from, is_current
                    FROM dim_customer
                    WHERE customer_id = :customer_id
                    ORDER BY version
                """),
                {'customer_id': customer_id}
            ).fetchall()

            logger.info("Current versions in warehouse:")
            for v in versions:
                status = "CURRENT" if v[4] else "EXPIRED"
                logger.info(f"  Version {v[0]}: {v[1]}, {v[2]} [{status}]")

        logger.info("\n--- Updating customer address ---")

        # Update customer address
        new_address = "456 New Street"
        new_city = "New City"

        conn.execute(
            text("""
                UPDATE customers
                SET address = :address, city = :city, updated_at = CURRENT_TIMESTAMP
                WHERE customer_id = :customer_id
            """),
            {
                'customer_id': customer_id,
                'address': new_address,
                'city': new_city
            }
        )
        conn.commit()

        logger.info(f"✓ Updated address to: {new_address}, {new_city}")
        logger.info("⏳ Waiting for CDC to process (5 seconds)...")
        time.sleep(5)

        # Check new versions
        with warehouse_engine.connect() as wh_conn:
            versions = wh_conn.execute(
                text("""
                    SELECT version, address, city, valid_from, valid_to, is_current
                    FROM dim_customer
                    WHERE customer_id = :customer_id
                    ORDER BY version
                """),
                {'customer_id': customer_id}
            ).fetchall()

            logger.info("\n✓ New versions in warehouse:")
            for v in versions:
                status = "CURRENT" if v[5] else "EXPIRED"
                logger.info(f"  Version {v[0]}: {v[1]}, {v[2]} [{status}]")
                logger.info(f"    Valid: {v[3]} to {v[4]}")

        logger.info("\n=== Scenario completed ===")
        logger.info("Notice: Old version was end-dated, new version created with is_current=TRUE")


if __name__ == '__main__':
    run_scenario()
