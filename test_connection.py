"""
Test database and Kafka connections
"""
import logging
from db_config import get_source_engine, get_warehouse_engine, KAFKA_CONFIG
from sqlalchemy import text
from kafka import KafkaConsumer
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_source_db():
    """Test source database connection"""
    logger.info("Testing source database connection...")
    try:
        engine = get_source_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            logger.info("✓ Source database connection OK")

            # Check tables
            tables = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)).fetchall()
            logger.info(f"  Tables: {[t[0] for t in tables]}")
            return True
    except Exception as e:
        logger.error(f"✗ Source database connection failed: {e}")
        return False


def test_warehouse_db():
    """Test warehouse database connection"""
    logger.info("\nTesting warehouse database connection...")
    try:
        engine = get_warehouse_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            logger.info("✓ Warehouse database connection OK")

            # Check tables
            tables = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)).fetchall()
            logger.info(f"  Tables: {[t[0] for t in tables]}")
            return True
    except Exception as e:
        logger.error(f"✗ Warehouse database connection failed: {e}")
        return False


def test_kafka():
    """Test Kafka connection"""
    logger.info("\nTesting Kafka connection...")
    try:
        # Try to connect and list topics
        consumer = KafkaConsumer(
            bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
            consumer_timeout_ms=5000
        )
        topics = consumer.topics()
        logger.info("✓ Kafka connection OK")
        logger.info(f"  Available topics: {list(topics)}")
        consumer.close()
        return True
    except Exception as e:
        logger.error(f"✗ Kafka connection failed: {e}")
        return False


def main():
    logger.info("=== Testing Connections ===\n")

    results = {
        'source_db': test_source_db(),
        'warehouse_db': test_warehouse_db(),
        'kafka': test_kafka()
    }

    logger.info("\n=== Summary ===")
    for service, status in results.items():
        status_icon = "✓" if status else "✗"
        logger.info(f"{status_icon} {service}: {'OK' if status else 'FAILED'}")

    all_ok = all(results.values())
    if all_ok:
        logger.info("\n✅ All connections successful!")
    else:
        logger.info("\n⚠️ Some connections failed. Check configuration.")

    return all_ok


if __name__ == '__main__':
    main()
