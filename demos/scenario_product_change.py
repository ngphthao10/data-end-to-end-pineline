"""
Scenario 2: Product Price Change (SCD Type 2)

Demonstrates how SCD Type 2 tracks product price changes for historical analysis.
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

    logger.info("=== Scenario 2: Product Price Change ===\n")

    with source_engine.connect() as conn:
        # Get a random product
        result = conn.execute(
            text("SELECT product_id, product_name, price, cost FROM products LIMIT 1")
        ).fetchone()

        if not result:
            logger.error("No products found in database")
            return

        product_id = result[0]
        name = result[1]
        old_price = float(result[2])
        cost = float(result[3])

        logger.info(f"Product: {name} (ID: {product_id})")
        logger.info(f"Current Price: ${old_price:.2f}")
        logger.info(f"Cost: ${cost:.2f}\n")

        # Check current version in warehouse
        with warehouse_engine.connect() as wh_conn:
            versions = wh_conn.execute(
                text("""
                    SELECT version, price, cost, margin_percentage, valid_from, is_current
                    FROM dim_product
                    WHERE product_id = :product_id
                    ORDER BY version
                """),
                {'product_id': product_id}
            ).fetchall()

            logger.info("Current versions in warehouse:")
            for v in versions:
                status = "CURRENT" if v[5] else "EXPIRED"
                logger.info(f"  Version {v[0]}: Price=${v[1]:.2f}, Margin={v[3]:.2f}% [{status}]")

        logger.info("\n--- Increasing product price ---")

        # Increase price by 20%
        new_price = round(old_price * 1.20, 2)

        conn.execute(
            text("""
                UPDATE products
                SET price = :price, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = :product_id
            """),
            {
                'product_id': product_id,
                'price': new_price
            }
        )
        conn.commit()

        logger.info(f"✓ Updated price from ${old_price:.2f} to ${new_price:.2f} (+20%)")
        logger.info("⏳ Waiting for CDC to process (5 seconds)...")
        time.sleep(5)

        # Check new versions
        with warehouse_engine.connect() as wh_conn:
            versions = wh_conn.execute(
                text("""
                    SELECT version, price, cost, margin_percentage, valid_from, valid_to, is_current
                    FROM dim_product
                    WHERE product_id = :product_id
                    ORDER BY version
                """),
                {'product_id': product_id}
            ).fetchall()

            logger.info("\n✓ New versions in warehouse:")
            for v in versions:
                status = "CURRENT" if v[6] else "EXPIRED"
                margin_change = f"Margin: {v[3]:.2f}%"
                logger.info(f"  Version {v[0]}: ${v[1]:.2f} - {margin_change} [{status}]")
                logger.info(f"    Valid: {v[4]} to {v[5]}")

        logger.info("\n=== Scenario completed ===")
        logger.info("Notice: Price change created new version. Historical orders preserve old price.")


if __name__ == '__main__':
    run_scenario()
