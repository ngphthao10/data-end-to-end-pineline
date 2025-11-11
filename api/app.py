from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import get_warehouse_engine
from sqlalchemy import text
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

warehouse_engine = get_warehouse_engine()


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
            '/api/products/<product_id>/history': 'Get product price history (SCD)'
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
