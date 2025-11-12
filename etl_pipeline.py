import json
import logging
from kafka import KafkaConsumer
from db_config import get_warehouse_engine, KAFKA_CONFIG
from scd_processor import SCDProcessor
from sqlalchemy import text
from datetime import datetime
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

    def start_consumer(self):
        """Initialize Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                'ecommerce.public.customers',
                'ecommerce.public.products',
                'ecommerce.public.orders',
                'ecommerce.public.order_items',
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                group_id=KAFKA_CONFIG['group_id'],
                auto_offset_reset=KAFKA_CONFIG['auto_offset_reset'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                enable_auto_commit=True
            )
            logger.info("Kafka consumer started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            return False

    def process_customer_event(self, event):
        """Process customer CDC event"""
        try:
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
                logger.info(">>> Calling scd_processor.process_customer_scd2")
                self.scd_processor.process_customer_scd2(customer_data, operation)
                logger.info(f"✓ Processed customer event: {operation} - ID {customer_data.get('customer_id')}")
        except Exception as e:
            logger.error(f"ERROR processing customer event: {e}", exc_info=True)

    def process_product_event(self, event):
        """Process product CDC event"""
        try:
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
        except Exception as e:
            logger.error(f"ERROR processing product event: {e}", exc_info=True)

    def process_order_item_event(self, event):
        """Process order_items CDC event and load to fact table"""
        try:
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

        except Exception as e:
            logger.error(f"Error processing order_item event: {e}")

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

    def run(self):
        """Main pipeline execution loop"""
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
                event = message.value

                logger.info(f"✓ Received event from {topic} - First 200 chars: {str(event)[:200]}")

                if topic == 'ecommerce.public.customers':
                    self.process_customer_event(event)
                elif topic == 'ecommerce.public.products':
                    self.process_product_event(event)
                elif topic == 'ecommerce.public.order_items':
                    self.process_order_item_event(event)
                # orders table is processed indirectly through order_items

        except KeyboardInterrupt:
            logger.info("ETL Pipeline stopped by user")
        except Exception as e:
            logger.error(f"ETL Pipeline error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
            logger.info("ETL Pipeline shut down")


if __name__ == '__main__':
    pipeline = ETLPipeline()
    pipeline.run()
