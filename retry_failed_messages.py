#!/usr/bin/env python3
"""
Retry failed messages from the failed_messages table

This script can be run manually or scheduled as a cron job to retry
messages that failed during processing.
"""

import json
import logging
from datetime import datetime
from sqlalchemy import text
from db_config import get_warehouse_engine
from scd_processor import SCDProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FailedMessageRetryProcessor:
    """Process failed messages for retry"""

    def __init__(self):
        self.warehouse_engine = get_warehouse_engine()
        self.scd_processor = SCDProcessor(self.warehouse_engine)

    def get_messages_to_retry(self, limit=100):
        """Get messages that are ready for retry"""
        with self.warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT failed_message_id, topic, partition, message_offset,
                           message_value, retry_count, max_retries
                    FROM failed_messages
                    WHERE status = 'pending'
                      AND retry_count < max_retries
                      AND (next_retry_at IS NULL OR next_retry_at <= CURRENT_TIMESTAMP)
                    ORDER BY failed_at
                    LIMIT :limit
                """),
                {'limit': limit}
            )
            return result.fetchall()

    def process_customer_event(self, event):
        """Process customer CDC event (same logic as ETL pipeline)"""
        if 'payload' in event:
            payload = event.get('payload', {})
            operation = payload.get('op', 'c')
            customer_data = payload.get('after', {}) if operation != 'd' else payload.get('before', {})
        else:
            operation = 'c' if event.get('before') is None else 'u'
            if event.get('after') is None:
                operation = 'd'
            customer_data = event.get('after', {}) if operation != 'd' else event.get('before', {})

        if customer_data:
            self.scd_processor.process_customer_scd2(customer_data, operation)
            logger.info(f"✓ Retried customer event: {operation} - ID {customer_data.get('customer_id')}")

    def process_product_event(self, event):
        """Process product CDC event (same logic as ETL pipeline)"""
        if 'payload' in event:
            payload = event.get('payload', {})
            operation = payload.get('op', 'c')
            product_data = payload.get('after', {}) if operation != 'd' else payload.get('before', {})
        else:
            operation = 'c' if event.get('before') is None else 'u'
            if event.get('after') is None:
                operation = 'd'
            product_data = event.get('after', {}) if operation != 'd' else event.get('before', {})

        if product_data:
            self.scd_processor.process_product_scd2(product_data, operation)
            logger.info(f"✓ Retried product event: {operation} - ID {product_data.get('product_id')}")

    def mark_as_resolved(self, failed_message_id):
        """Mark message as successfully resolved"""
        with self.warehouse_engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE failed_messages
                    SET status = 'resolved',
                        resolved_at = CURRENT_TIMESTAMP
                    WHERE failed_message_id = :id
                """),
                {'id': failed_message_id}
            )
            conn.commit()

    def mark_as_dead_letter(self, failed_message_id, error_msg):
        """Mark message as dead letter (max retries exceeded)"""
        with self.warehouse_engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE failed_messages
                    SET status = 'dead_letter',
                        error_message = :error_msg,
                        last_retry_at = CURRENT_TIMESTAMP
                    WHERE failed_message_id = :id
                """),
                {'id': failed_message_id, 'error_msg': error_msg}
            )
            conn.commit()

    def increment_retry_count(self, failed_message_id):
        """Increment retry count after failed attempt"""
        with self.warehouse_engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE failed_messages
                    SET retry_count = retry_count + 1,
                        last_retry_at = CURRENT_TIMESTAMP,
                        next_retry_at = CURRENT_TIMESTAMP + INTERVAL '15 minutes'
                    WHERE failed_message_id = :id
                """),
                {'id': failed_message_id}
            )
            conn.commit()

    def retry_failed_messages(self):
        """Main retry loop"""
        logger.info("Starting failed message retry processor...")

        messages = self.get_messages_to_retry()
        logger.info(f"Found {len(messages)} messages to retry")

        success_count = 0
        failed_count = 0
        dead_letter_count = 0

        for msg in messages:
            failed_message_id, topic, partition, offset, message_value, retry_count, max_retries = msg

            logger.info(f"Retrying: {topic}[{partition}]@{offset} (attempt {retry_count + 1}/{max_retries})")

            try:
                # Parse message
                event = json.loads(message_value) if isinstance(message_value, str) else message_value

                # Process based on topic
                if topic == 'ecommerce.public.customers':
                    self.process_customer_event(event)
                elif topic == 'ecommerce.public.products':
                    self.process_product_event(event)
                # Add more topics as needed

                # Mark as resolved
                self.mark_as_resolved(failed_message_id)
                success_count += 1
                logger.info(f"✅ Successfully retried: {topic}[{partition}]@{offset}")

            except Exception as e:
                logger.error(f"❌ Retry failed: {topic}[{partition}]@{offset} - {str(e)}")

                # Check if max retries exceeded
                if retry_count + 1 >= max_retries:
                    self.mark_as_dead_letter(failed_message_id, str(e))
                    dead_letter_count += 1
                    logger.warning(f"⚰️  Moved to dead letter: {topic}[{partition}]@{offset}")
                else:
                    self.increment_retry_count(failed_message_id)
                    failed_count += 1

        logger.info(f"Retry completed: {success_count} succeeded, {failed_count} failed, {dead_letter_count} dead letters")


if __name__ == '__main__':
    processor = FailedMessageRetryProcessor()
    processor.retry_failed_messages()
