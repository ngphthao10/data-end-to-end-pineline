from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import subprocess
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import get_warehouse_engine, get_source_engine, KAFKA_CONFIG
from sqlalchemy import text
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

warehouse_engine = get_warehouse_engine()
source_engine = get_source_engine()


@app.route('/')
def home():
    return jsonify({
        'message': 'E-commerce Data Warehouse API',
        'version': '1.0.0',
        'endpoints': {
            '/api/metrics/daily-revenue': 'Get daily revenue',
            '/api/metrics/top-products': 'Get top selling products',
            '/api/metrics/top-customers': 'Get top customers by revenue',
            '/api/metrics/sales-by-category': 'Get sales by category',
            '/api/customers/<customer_id>/history': 'Get customer history (SCD)',
            '/api/products/<product_id>/history': 'Get product price history (SCD)',
            '/api/monitoring/kafka-offsets': 'Get Kafka consumer offset status',
            '/api/monitoring/failed-messages': 'Get failed messages',
            '/api/monitoring/failed-messages/retry': 'Retry failed messages'
        }
    })


@app.route('/api/metrics/daily-revenue', methods=['GET'])
def daily_revenue():
    """Get daily revenue for the last N days"""
    days = request.args.get('days', 30, type=int)

    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        d.date,
                        d.day_of_week,
                        COUNT(DISTINCT f.order_id) as num_orders,
                        SUM(f.quantity) as total_items,
                        SUM(f.line_total) as revenue
                    FROM fact_orders f
                    JOIN dim_date d ON f.date_key = d.date_key
                    WHERE d.date >= CURRENT_DATE - INTERVAL ':days days'
                    GROUP BY d.date, d.day_of_week
                    ORDER BY d.date DESC
                """),
                {'days': days}
            )

            data = [
                {
                    'date': str(row[0]),
                    'day_of_week': row[1].strip(),
                    'num_orders': row[2],
                    'total_items': row[3],
                    'revenue': float(row[4]) if row[4] else 0
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'data': data
            })

    except Exception as e:
        logger.error(f"Error in daily_revenue: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metrics/top-products', methods=['GET'])
def top_products():
    """Get top selling products"""
    limit = request.args.get('limit', 10, type=int)

    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        p.product_id,
                        p.product_name,
                        p.category,
                        p.brand,
                        p.price,
                        SUM(f.quantity) as units_sold,
                        SUM(f.line_total) as total_revenue
                    FROM fact_orders f
                    JOIN dim_product p ON f.product_key = p.product_key
                    WHERE p.is_current = TRUE
                    GROUP BY p.product_id, p.product_name, p.category, p.brand, p.price
                    ORDER BY total_revenue DESC
                    LIMIT :limit
                """),
                {'limit': limit}
            )

            data = [
                {
                    'product_id': row[0],
                    'product_name': row[1],
                    'category': row[2],
                    'brand': row[3],
                    'current_price': float(row[4]) if row[4] else 0,
                    'units_sold': row[5],
                    'total_revenue': float(row[6]) if row[6] else 0
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'data': data
            })

    except Exception as e:
        logger.error(f"Error in top_products: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metrics/top-customers', methods=['GET'])
def top_customers():
    """Get top customers by lifetime value"""
    limit = request.args.get('limit', 10, type=int)

    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        c.customer_id,
                        c.first_name || ' ' || c.last_name as customer_name,
                        c.email,
                        c.city,
                        c.country,
                        COUNT(DISTINCT f.order_id) as total_orders,
                        SUM(f.line_total) as lifetime_value
                    FROM fact_orders f
                    JOIN dim_customer c ON f.customer_key = c.customer_key
                    WHERE c.is_current = TRUE
                    GROUP BY c.customer_id, customer_name, c.email, c.city, c.country
                    ORDER BY lifetime_value DESC
                    LIMIT :limit
                """),
                {'limit': limit}
            )

            data = [
                {
                    'customer_id': row[0],
                    'customer_name': row[1],
                    'email': row[2],
                    'city': row[3],
                    'country': row[4],
                    'total_orders': row[5],
                    'lifetime_value': float(row[6]) if row[6] else 0
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'data': data
            })

    except Exception as e:
        logger.error(f"Error in top_customers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metrics/sales-by-category', methods=['GET'])
def sales_by_category():
    """Get sales breakdown by product category"""
    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        p.category,
                        COUNT(DISTINCT f.order_id) as num_orders,
                        SUM(f.quantity) as units_sold,
                        SUM(f.line_total) as revenue,
                        AVG(f.unit_price) as avg_price
                    FROM fact_orders f
                    JOIN dim_product p ON f.product_key = p.product_key
                    WHERE p.is_current = TRUE
                    GROUP BY p.category
                    ORDER BY revenue DESC
                """)
            )

            data = [
                {
                    'category': row[0],
                    'num_orders': row[1],
                    'units_sold': row[2],
                    'revenue': float(row[3]) if row[3] else 0,
                    'avg_price': float(row[4]) if row[4] else 0
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'data': data
            })

    except Exception as e:
        logger.error(f"Error in sales_by_category: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/customers/<int:customer_id>/history', methods=['GET'])
def customer_history(customer_id):
    """Get customer's SCD history (all versions)"""
    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        customer_key,
                        customer_id,
                        first_name,
                        last_name,
                        email,
                        phone,
                        address,
                        city,
                        country,
                        valid_from,
                        valid_to,
                        is_current,
                        version
                    FROM dim_customer
                    WHERE customer_id = :customer_id
                    ORDER BY version ASC
                """),
                {'customer_id': customer_id}
            )

            data = [
                {
                    'customer_key': row[0],
                    'customer_id': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'email': row[4],
                    'phone': row[5],
                    'address': row[6],
                    'city': row[7],
                    'country': row[8],
                    'valid_from': str(row[9]),
                    'valid_to': str(row[10]),
                    'is_current': row[11],
                    'version': row[12]
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'customer_id': customer_id,
                'versions': len(data),
                'data': data
            })

    except Exception as e:
        logger.error(f"Error in customer_history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products/<int:product_id>/history', methods=['GET'])
def product_history(product_id):
    """Get product's price history (SCD Type 2)"""
    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        product_key,
                        product_id,
                        product_name,
                        category,
                        brand,
                        price,
                        cost,
                        margin_percentage,
                        valid_from,
                        valid_to,
                        is_current,
                        version
                    FROM dim_product
                    WHERE product_id = :product_id
                    ORDER BY version ASC
                """),
                {'product_id': product_id}
            )

            data = [
                {
                    'product_key': row[0],
                    'product_id': row[1],
                    'product_name': row[2],
                    'category': row[3],
                    'brand': row[4],
                    'price': float(row[5]) if row[5] else 0,
                    'cost': float(row[6]) if row[6] else 0,
                    'margin_percentage': float(row[7]) if row[7] else 0,
                    'valid_from': str(row[8]),
                    'valid_to': str(row[9]),
                    'is_current': row[10],
                    'version': row[11]
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'product_id': product_id,
                'versions': len(data),
                'data': data
            })

    except Exception as e:
        logger.error(f"Error in product_history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cdc/stats', methods=['GET'])
def cdc_stats():
    """Get CDC synchronization statistics"""
    try:
        with source_engine.connect() as source_conn, warehouse_engine.connect() as warehouse_conn:
            # Count records in source
            source_customers = source_conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
            source_products = source_conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
            source_orders = source_conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()

            # Count current records in warehouse
            warehouse_customers = warehouse_conn.execute(
                text("SELECT COUNT(DISTINCT customer_id) FROM dim_customer WHERE is_current = TRUE")
            ).scalar()
            warehouse_products = warehouse_conn.execute(
                text("SELECT COUNT(DISTINCT product_id) FROM dim_product WHERE is_current = TRUE")
            ).scalar()
            warehouse_orders = warehouse_conn.execute(
                text("SELECT COUNT(DISTINCT order_id) FROM fact_orders")
            ).scalar()

            # Calculate sync percentage for orders
            orders_sync_percentage = (warehouse_orders / source_orders * 100) if source_orders > 0 else 100

            # Consider in sync if:
            # - Customers and Products are 100% synced
            # - Orders are at least 75% synced (allows for historical data gaps)
            in_sync = (
                source_customers == warehouse_customers and
                source_products == warehouse_products and
                orders_sync_percentage >= 75
            )

            return jsonify({
                'success': True,
                'data': {
                    'source': {
                        'customers': source_customers,
                        'products': source_products,
                        'orders': source_orders
                    },
                    'warehouse': {
                        'customers': warehouse_customers,
                        'products': warehouse_products,
                        'orders': warehouse_orders
                    },
                    'sync_percentages': {
                        'customers': 100.0 if source_customers == warehouse_customers else (warehouse_customers / source_customers * 100 if source_customers > 0 else 0),
                        'products': 100.0 if source_products == warehouse_products else (warehouse_products / source_products * 100 if source_products > 0 else 0),
                        'orders': round(orders_sync_percentage, 2)
                    },
                    'in_sync': in_sync
                }
            })
    except Exception as e:
        logger.error(f"Error in cdc_stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cdc/recent-changes', methods=['GET'])
def recent_changes():
    """Get recent SCD changes from warehouse"""
    limit = request.args.get('limit', 20, type=int)

    try:
        with warehouse_engine.connect() as conn:
            # Get recent customer changes
            customer_changes = conn.execute(
                text("""
                    SELECT
                        'customer' as entity_type,
                        customer_id as entity_id,
                        first_name || ' ' || last_name as entity_name,
                        email,
                        valid_from as change_time,
                        version,
                        is_current,
                        CASE
                            WHEN version = 1 THEN 'create'
                            WHEN is_current = FALSE THEN 'update'
                            ELSE 'current'
                        END as change_type
                    FROM dim_customer
                    ORDER BY valid_from DESC
                    LIMIT :limit
                """),
                {'limit': limit}
            )

            # Get recent product changes
            product_changes = conn.execute(
                text("""
                    SELECT
                        'product' as entity_type,
                        product_id as entity_id,
                        product_name as entity_name,
                        price,
                        valid_from as change_time,
                        version,
                        is_current,
                        CASE
                            WHEN version = 1 THEN 'create'
                            WHEN is_current = FALSE THEN 'update'
                            ELSE 'current'
                        END as change_type
                    FROM dim_product
                    ORDER BY valid_from DESC
                    LIMIT :limit
                """),
                {'limit': limit}
            )

            customer_data = [
                {
                    'entity_type': row[0],
                    'entity_id': row[1],
                    'entity_name': row[2],
                    'email': row[3],
                    'change_time': str(row[4]),
                    'version': row[5],
                    'is_current': row[6],
                    'change_type': row[7]
                }
                for row in customer_changes
            ]

            product_data = [
                {
                    'entity_type': row[0],
                    'entity_id': row[1],
                    'entity_name': row[2],
                    'price': float(row[3]) if row[3] else 0,
                    'change_time': str(row[4]),
                    'version': row[5],
                    'is_current': row[6],
                    'change_type': row[7]
                }
                for row in product_changes
            ]

            # Combine and sort by change_time
            all_changes = customer_data + product_data
            all_changes.sort(key=lambda x: x['change_time'], reverse=True)

            return jsonify({
                'success': True,
                'data': all_changes[:limit]
            })

    except Exception as e:
        logger.error(f"Error in recent_changes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all current customers from warehouse"""
    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        customer_id,
                        first_name,
                        last_name,
                        email,
                        phone,
                        city,
                        country
                    FROM dim_customer
                    WHERE is_current = TRUE
                    ORDER BY customer_id
                """)
            )

            data = [
                {
                    'customer_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'email': row[3],
                    'phone': row[4],
                    'city': row[5],
                    'country': row[6]
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'data': data
            })
    except Exception as e:
        logger.error(f"Error in get_customers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all current products from warehouse"""
    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        product_id,
                        product_name,
                        category,
                        brand,
                        price
                    FROM dim_product
                    WHERE is_current = TRUE
                    ORDER BY product_id
                """)
            )

            data = [
                {
                    'product_id': row[0],
                    'product_name': row[1],
                    'category': row[2],
                    'brand': row[3],
                    'price': float(row[4]) if row[4] else 0
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'data': data
            })
    except Exception as e:
        logger.error(f"Error in get_products: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/monitoring/kafka-offsets', methods=['GET'])
def kafka_offsets():
    """Get Kafka consumer offset status and lag from failed_messages summary"""
    try:
        # Since kafka tools are not available in API container,
        # we'll provide a simpler view based on failed messages
        with warehouse_engine.connect() as conn:
            # Get unique topics from failed messages
            result = conn.execute(
                text("""
                    SELECT
                        topic,
                        partition,
                        COUNT(*) as failed_count,
                        MIN(message_offset) as min_offset,
                        MAX(message_offset) as max_offset
                    FROM failed_messages
                    WHERE status IN ('pending', 'retrying')
                    GROUP BY topic, partition
                    ORDER BY topic, partition
                """)
            )

            data = []
            for row in result:
                data.append({
                    'topic': row[0],
                    'partition': row[1],
                    'failed_count': row[2],
                    'min_offset': row[3],
                    'max_offset': row[4],
                    'lag': row[2]  # Use failed count as proxy for lag
                })

        # If no failed messages, show a healthy state
        if not data:
            # Show common topics as healthy
            data = [
                {'topic': 'ecommerce.public.customers', 'partition': 0, 'failed_count': 0, 'lag': 0},
                {'topic': 'ecommerce.public.products', 'partition': 0, 'failed_count': 0, 'lag': 0},
                {'topic': 'ecommerce.public.orders', 'partition': 0, 'failed_count': 0, 'lag': 0},
                {'topic': 'ecommerce.public.order_items', 'partition': 0, 'failed_count': 0, 'lag': 0},
            ]

        return jsonify({
            'success': True,
            'consumer_group': KAFKA_CONFIG['group_id'],
            'note': 'Offset data based on failed messages. For detailed offset info, use Kafka tools directly.',
            'data': data
        })

    except Exception as e:
        logger.error(f"Error in kafka_offsets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/monitoring/failed-messages', methods=['GET'])
def get_failed_messages():
    """Get all failed messages with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', None, type=str)

    try:
        with warehouse_engine.connect() as conn:
            # Build WHERE clause
            where_clause = ""
            params = {}

            if status:
                where_clause = "WHERE status = :status"
                params['status'] = status

            # Get total count
            count_query = f"SELECT COUNT(*) FROM failed_messages {where_clause}"
            total = conn.execute(text(count_query), params).scalar()

            # Get paginated data
            offset = (page - 1) * per_page
            params['limit'] = per_page
            params['offset'] = offset

            result = conn.execute(
                text(f"""
                    SELECT
                        failed_message_id,
                        topic,
                        partition,
                        message_offset,
                        message_timestamp,
                        error_type,
                        error_message,
                        retry_count,
                        max_retries,
                        status,
                        failed_at,
                        last_retry_at,
                        next_retry_at
                    FROM failed_messages
                    {where_clause}
                    ORDER BY failed_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                params
            )

            data = [
                {
                    'id': row[0],
                    'topic': row[1],
                    'partition': row[2],
                    'offset': row[3],
                    'timestamp': str(row[4]) if row[4] else None,
                    'error_type': row[5],
                    'error_message': row[6],
                    'retry_count': row[7],
                    'max_retries': row[8],
                    'status': row[9],
                    'failed_at': str(row[10]),
                    'last_retry_at': str(row[11]) if row[11] else None,
                    'next_retry_at': str(row[12]) if row[12] else None
                }
                for row in result
            ]

            return jsonify({
                'success': True,
                'data': data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })

    except Exception as e:
        logger.error(f"Error in get_failed_messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/monitoring/failed-messages/summary', methods=['GET'])
def failed_messages_summary():
    """Get summary of failed messages"""
    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM v_failed_messages_summary
                """)
            )

            data = [
                {
                    'topic': row[0],
                    'status': row[1],
                    'error_type': row[2],
                    'message_count': row[3],
                    'first_failure': str(row[4]) if row[4] else None,
                    'last_failure': str(row[5]) if row[5] else None,
                    'avg_retry_count': float(row[6]) if row[6] else 0,
                    'dead_letter_count': row[7]
                }
                for row in result
            ]

            # Get total counts by status
            status_counts = conn.execute(
                text("""
                    SELECT status, COUNT(*) as count
                    FROM failed_messages
                    GROUP BY status
                """)
            )

            status_data = {row[0]: row[1] for row in status_counts}

            return jsonify({
                'success': True,
                'summary': data,
                'status_counts': status_data
            })

    except Exception as e:
        logger.error(f"Error in failed_messages_summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/monitoring/failed-messages/<int:message_id>', methods=['GET'])
def get_failed_message_detail(message_id):
    """Get detailed information about a specific failed message"""
    try:
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        failed_message_id,
                        topic,
                        partition,
                        message_offset,
                        message_timestamp,
                        message_key,
                        message_value,
                        error_type,
                        error_message,
                        error_stacktrace,
                        retry_count,
                        max_retries,
                        last_retry_at,
                        next_retry_at,
                        status,
                        resolution_notes,
                        failed_at,
                        resolved_at
                    FROM failed_messages
                    WHERE failed_message_id = :id
                """),
                {'id': message_id}
            ).fetchone()

            if not result:
                return jsonify({'success': False, 'error': 'Message not found'}), 404

            data = {
                'id': result[0],
                'topic': result[1],
                'partition': result[2],
                'offset': result[3],
                'timestamp': str(result[4]) if result[4] else None,
                'message_key': result[5],
                'message_value': result[6],  # This is JSONB
                'error_type': result[7],
                'error_message': result[8],
                'error_stacktrace': result[9],
                'retry_count': result[10],
                'max_retries': result[11],
                'last_retry_at': str(result[12]) if result[12] else None,
                'next_retry_at': str(result[13]) if result[13] else None,
                'status': result[14],
                'resolution_notes': result[15],
                'failed_at': str(result[16]),
                'resolved_at': str(result[17]) if result[17] else None
            }

            return jsonify({
                'success': True,
                'data': data
            })

    except Exception as e:
        logger.error(f"Error in get_failed_message_detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/monitoring/failed-messages/<int:message_id>/retry', methods=['POST'])
def retry_failed_message(message_id):
    """Retry a specific failed message"""
    try:
        # Import retry logic
        from retry_failed_messages import FailedMessageRetryProcessor

        processor = FailedMessageRetryProcessor()

        # Get the message
        with warehouse_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT message_value, topic
                    FROM failed_messages
                    WHERE failed_message_id = :id AND status = 'pending'
                """),
                {'id': message_id}
            ).fetchone()

            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Message not found or not in pending status'
                }), 404

            message_value = result[0]
            topic = result[1]

            # Parse and retry
            event = json.loads(message_value) if isinstance(message_value, str) else message_value

            # Process based on topic
            if topic == 'ecommerce.public.customers':
                processor.process_customer_event(event)
            elif topic == 'ecommerce.public.products':
                processor.process_product_event(event)

            # Mark as resolved
            processor.mark_as_resolved(message_id)

            return jsonify({
                'success': True,
                'message': f'Message {message_id} retried successfully'
            })

    except Exception as e:
        logger.error(f"Error retrying message {message_id}: {e}")
        # Increment retry count
        try:
            from retry_failed_messages import FailedMessageRetryProcessor
            processor = FailedMessageRetryProcessor()
            processor.increment_retry_count(message_id)
        except:
            pass

        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/monitoring/failed-messages/retry-all', methods=['POST'])
def retry_all_failed_messages():
    """Retry all pending failed messages"""
    try:
        # Run retry script
        result = subprocess.run(
            ['python', '/app/retry_failed_messages.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr if result.returncode != 0 else None
        })

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Retry process timeout'}), 500
    except Exception as e:
        logger.error(f"Error in retry_all_failed_messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
