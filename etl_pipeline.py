import json
import logging
import traceback
from kafka import KafkaConsumer
from db_config import get_warehouse_engine, KAFKA_CONFIG
from scd_processor import SCDProcessor
from sqlalchemy import text
from datetime import datetime, timedelta
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """Main ETL Pipeline for processing CDC events"""

    def __init__(self):
        self.warehouse_engine = get_warehouse_engine()
        self.scd_processor = SCDProcessor(self.warehouse_engine)
        self.consumer = None
        self.warehouse_healthy = True  # Track warehouse health status

    def start_consumer(self):
        """Initialize Kafka consumer with manual offset commit"""
        try:
            self.consumer = KafkaConsumer(
                'ecommerce.public.customers',
                'ecommerce.public.products',
                'ecommerce.public.orders',
                'ecommerce.public.order_items',
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                group_id=KAFKA_CONFIG['group_id'],
                auto_offset_reset=KAFKA_CONFIG['auto_offset_reset'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m is not None else None,
                enable_auto_commit=False,  # Manual commit for better error handling
                max_poll_records=10,  # Process in smaller batches
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            logger.info("Kafka consumer started successfully (manual offset commit enabled)")
            return True
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            return False

    def process_customer_event(self, event):
        """Process customer CDC event"""
        logger.info(">>> Entering process_customer_event")
        # Handle both formats: with and without payload wrapper
        if 'payload' in event:
            payload = event.get('payload', {})
            operation = payload.get('op', 'c')
            customer_data = payload.get('after', {}) if operation != 'd' else payload.get('before', {})
        else:
            # Direct format from Debezium without unwrap transform
            operation = 'c' if event.get('before') is None else 'u'
            if event.get('after') is None:
                operation = 'd'
            customer_data = event.get('after', {}) if operation != 'd' else event.get('before', {})

        logger.info(f">>> Customer data: {customer_data.get('customer_id') if customer_data else 'None'}, operation: {operation}")
        if customer_data:
            # Validation: Email must contain '@' and domain
            email = customer_data.get('email', '')
            if 'ERROR' in email.upper():
                raise ValueError(f"Validation failed: Email '{email}' contains forbidden keyword 'ERROR'")

            logger.info(">>> Calling scd_processor.process_customer_scd2")
            self.scd_processor.process_customer_scd2(customer_data, operation)
            logger.info(f"✓ Processed customer event: {operation} - ID {customer_data.get('customer_id')}")

    def process_product_event(self, event):
        """Process product CDC event"""
        logger.info(">>> Entering process_product_event")
        # Handle both formats
        if 'payload' in event:
            payload = event.get('payload', {})
            operation = payload.get('op', 'c')
            product_data = payload.get('after', {}) if operation != 'd' else payload.get('before', {})
        else:
            operation = 'c' if event.get('before') is None else 'u'
            if event.get('after') is None:
                operation = 'd'
            product_data = event.get('after', {}) if operation != 'd' else event.get('before', {})

        logger.info(f">>> Product data: {product_data.get('product_id') if product_data else 'None'}, operation: {operation}")
        if product_data:
            logger.info(">>> Calling scd_processor.process_product_scd2")
            self.scd_processor.process_product_scd2(product_data, operation)
            logger.info(f"✓ Processed product event: {operation} - ID {product_data.get('product_id')}")

    def process_order_item_event(self, event):
        """Process order_items CDC event and load to fact table"""
        # Handle both formats
        if 'payload' in event:
            payload = event.get('payload', {})
            operation = payload.get('op', 'c')
            order_item_data = payload.get('after', {})
        else:
            operation = 'c' if event.get('before') is None else 'u'
            if event.get('after') is None:
                operation = 'd'
            order_item_data = event.get('after', {})

        if operation != 'c':
            # Only process inserts for fact table
            return

        if not order_item_data:
            return

        # Get order details to find customer_id and order_date
        order_id = order_item_data.get('order_id')
        product_id = order_item_data.get('product_id')

        with self.warehouse_engine.connect() as conn:
            # Get order info from source (ideally cache this)
            order_info = self.get_order_info(order_id)

            if not order_info:
                logger.warning(f"Order {order_id} not found, skipping fact load")
                return

            customer_id = order_info['customer_id']
            order_date = order_info['order_date']
            order_status = order_info['status']

            # Lookup dimension keys
            customer_key = self.scd_processor.get_current_customer_key(customer_id)
            product_key = self.scd_processor.get_current_product_key(product_id)
            date_key = self.scd_processor.get_date_key(order_date)

            if not customer_key:
                logger.warning(f"Customer key not found for customer_id {customer_id}")
                return

            if not product_key:
                logger.warning(f"Product key not found for product_id {product_id}")
                return

            # Insert into fact table
            conn.execute(
                text("""
                    INSERT INTO fact_orders (
                        order_id, order_item_id, customer_key, product_key,
                        date_key, quantity, unit_price, line_total, order_status
                    ) VALUES (
                        :order_id, :order_item_id, :customer_key, :product_key,
                        :date_key, :quantity, :unit_price, :line_total, :order_status
                    )
                """),
                {
                    'order_id': order_id,
                    'order_item_id': order_item_data.get('order_item_id'),
                    'customer_key': customer_key,
                    'product_key': product_key,
                    'date_key': date_key,
                    'quantity': order_item_data.get('quantity'),
                    'unit_price': float(order_item_data.get('unit_price', 0)),
                    'line_total': float(order_item_data.get('line_total', 0)),
                    'order_status': order_status
                }
            )
            conn.commit()
            logger.info(f"Loaded fact: order_item_id {order_item_data.get('order_item_id')}")

    def get_order_info(self, order_id):
        """Get order information (customer_id, order_date, status)"""
        # In production, you might want to cache this or use a lookup service
        from db_config import get_source_engine
        source_engine = get_source_engine()

        try:
            with source_engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT customer_id, order_date, status
                        FROM orders
                        WHERE order_id = :order_id
                    """),
                    {'order_id': order_id}
                ).fetchone()

                if result:
                    return {
                        'customer_id': result[0],
                        'order_date': result[1],
                        'status': result[2]
                    }
        except Exception as e:
            logger.error(f"Error fetching order info: {e}")

        return None

    def check_warehouse_health(self):
        """Check if warehouse database is accessible"""
        try:
            with self.warehouse_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.debug(f"Warehouse health check failed: {e}")
            return False

    def save_failed_message(self, topic, partition, offset, message_value, error, timestamp=None):
        """Save failed message to database for later retry (only if warehouse is accessible)"""
        try:
            with self.warehouse_engine.connect() as conn:
                # Calculate next retry time (exponential backoff: 5min, 15min, 30min)
                retry_delays = [5, 15, 30]  # minutes

                conn.execute(
                    text("""
                        INSERT INTO failed_messages (
                            topic, partition, message_offset, message_timestamp,
                            message_value, error_type, error_message, error_stacktrace,
                            next_retry_at, status
                        ) VALUES (
                            :topic, :partition, :message_offset, :message_timestamp,
                            :message_value, :error_type, :error_message, :error_stacktrace,
                            :next_retry_at, 'pending'
                        )
                        ON CONFLICT (topic, partition, message_offset)
                        DO UPDATE SET
                            retry_count = failed_messages.retry_count + 1,
                            last_retry_at = CURRENT_TIMESTAMP,
                            error_message = EXCLUDED.error_message,
                            error_stacktrace = EXCLUDED.error_stacktrace,
                            next_retry_at = CURRENT_TIMESTAMP + INTERVAL '5 minutes',
                            status = CASE
                                WHEN failed_messages.retry_count + 1 >= failed_messages.max_retries
                                THEN 'dead_letter'
                                ELSE 'pending'
                            END
                    """),
                    {
                        'topic': topic,
                        'partition': partition,
                        'message_offset': offset,
                        'message_timestamp': timestamp or datetime.now(),
                        'message_value': json.dumps(message_value),
                        'error_type': type(error).__name__,
                        'error_message': str(error),
                        'error_stacktrace': traceback.format_exc(),
                        'next_retry_at': datetime.now() + timedelta(minutes=5)
                    }
                )
                conn.commit()
                logger.info(f"💾 Failed message saved to DB: {topic}[{partition}]@{offset}")
                return True
        except Exception as e:
            logger.error(f"⚠️  Could not save failed message to DB: {e}")
            logger.info(f"📝 Message will be reprocessed via Kafka offset tracking: {topic}[{partition}]@{offset}")
            # Don't raise - we rely on Kafka offset mechanism for retry
            return False

    def run(self):
        """Main pipeline execution loop with offset tracking and error handling"""
        logger.info("Starting ETL Pipeline...")

        # Wait for Kafka to be ready
        retry_count = 0
        while not self.start_consumer() and retry_count < 10:
            logger.info(f"Retrying Kafka connection... ({retry_count + 1}/10)")
            time.sleep(5)
            retry_count += 1

        if not self.consumer:
            logger.error("Failed to connect to Kafka after 10 retries. Exiting.")
            return

        logger.info("ETL Pipeline is running. Waiting for CDC events...")

        try:
            for message in self.consumer:
                topic = message.topic
                partition = message.partition
                offset = message.offset
                timestamp = datetime.fromtimestamp(message.timestamp / 1000) if message.timestamp else None
                event = message.value

                # Log offset information
                logger.info(f"📨 Processing message: topic={topic}, partition={partition}, offset={offset}, timestamp={timestamp}")

                # Skip None/tombstone messages but still commit offset
                if event is None:
                    logger.warning(f"Received None/tombstone message from {topic}[{partition}]@{offset}, skipping")
                    self.consumer.commit()
                    continue

                logger.debug(f"Message preview: {str(event)[:200]}...")

                # Process message with error handling
                processing_success = False
                try:
                    if topic == 'ecommerce.public.customers':
                        self.process_customer_event(event)
                        processing_success = True
                    elif topic == 'ecommerce.public.products':
                        self.process_product_event(event)
                        processing_success = True
                    elif topic == 'ecommerce.public.order_items':
                        self.process_order_item_event(event)
                        processing_success = True
                    # orders table is processed indirectly through order_items

                    if processing_success:
                        # Commit offset only on success
                        self.consumer.commit()
                        logger.info(f"✅ SUCCESS: {topic}[{partition}]@{offset} committed")

                except Exception as e:
                    logger.error(f"❌ FAILED: {topic}[{partition}]@{offset} - {type(e).__name__}: {str(e)}")

                    # Check warehouse health before trying to save failed message
                    warehouse_is_healthy = self.check_warehouse_health()
                    self.warehouse_healthy = warehouse_is_healthy

                    if warehouse_is_healthy:
                        # Warehouse is accessible - save failed message for tracking and manual retry
                        self.save_failed_message(topic, partition, offset, event, e, timestamp)
                        logger.info(f"✅ Failed message tracked in DB - can retry via UI")
                    else:
                        # Warehouse is down - cannot save to DB, rely on Kafka offset mechanism
                        logger.warning(f"⚠️  Warehouse unavailable - cannot save to failed_messages table")
                        logger.info(f"📨 Kafka will re-deliver this message on next consumer restart")

                    # DO NOT commit offset - Kafka will re-deliver this message
                    # on next consumer restart or seek
                    logger.warning(f"⚠️  Offset NOT committed - message will be retried")

                    # Optional: decide whether to continue or stop
                    # For now, we continue processing next messages
                    # You could also implement: break, raise, or skip N messages

        except KeyboardInterrupt:
            logger.info("ETL Pipeline stopped by user")
        except Exception as e:
            logger.error(f"ETL Pipeline fatal error: {e}", exc_info=True)
        finally:
            if self.consumer:
                self.consumer.close()
            logger.info("ETL Pipeline shut down")


if __name__ == '__main__':
    pipeline = ETLPipeline()
    pipeline.run()
