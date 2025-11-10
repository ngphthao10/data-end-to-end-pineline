from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from kafka import KafkaConsumer
import json
import threading
import queue
import requests

app = Flask(__name__)
CORS(app)

# Database connections
MYSQL_DB_URL = "mysql+pymysql://mysqluser:mysqlpw@localhost:3306/inventory"
POSTGRES_DB_URL = "postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/postgres"

mysql_engine = create_engine(MYSQL_DB_URL)
postgres_engine = create_engine(POSTGRES_DB_URL)

# Queue for CDC events
cdc_events_queue = queue.Queue(maxsize=100)

# Kafka consumer in background thread
def consume_cdc_events():
    """Background thread to consume Kafka CDC events."""
    try:
        print("Starting Kafka consumer...")
        consumer = KafkaConsumer(
            'dbserver1.inventory.customers',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='earliest',  # Read from beginning
            enable_auto_commit=True,
            group_id='web-dashboard-consumer',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None
        )
        print(f"Kafka consumer connected successfully. Topics: {consumer.topics()}")

        for message in consumer:
            if message.value:
                try:
                    event = message.value
                    payload = event.get('payload', {})

                    # Add to queue
                    if cdc_events_queue.full():
                        cdc_events_queue.get()  # Remove oldest

                    event_data = {
                        'op': payload.get('op'),
                        'before': payload.get('before'),
                        'after': payload.get('after'),
                        'timestamp': payload.get('ts_ms'),
                        'source': payload.get('source', {}).get('table')
                    }
                    cdc_events_queue.put(event_data)
                    print(f"CDC Event captured: op={event_data['op']}, source={event_data['source']}")
                except Exception as e:
                    print(f"Error processing CDC event: {e}")
    except Exception as e:
        print(f"Error initializing Kafka consumer: {e}")
        import traceback
        traceback.print_exc()

# Start background thread
consumer_thread = threading.Thread(target=consume_cdc_events, daemon=True)
consumer_thread.start()

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

@app.route('/api/mysql/customers', methods=['GET'])
def get_mysql_customers():
    """Get all customers from MySQL."""
    try:
        with mysql_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM customers ORDER BY id"))
            customers = [dict(row._mapping) for row in result]
            return jsonify(customers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/postgres/customers', methods=['GET'])
def get_postgres_customers():
    """Get all customers from PostgreSQL."""
    try:
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM customers ORDER BY id"))
            customers = [dict(row._mapping) for row in result]
            return jsonify(customers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics from both databases."""
    try:
        with mysql_engine.connect() as mysql_conn:
            mysql_count = mysql_conn.execute(text("SELECT COUNT(*) as count FROM customers")).scalar()

        with postgres_engine.connect() as pg_conn:
            postgres_count = pg_conn.execute(text("SELECT COUNT(*) as count FROM customers")).scalar()

        return jsonify({
            'mysql_count': mysql_count,
            'postgres_count': postgres_count,
            'in_sync': mysql_count == postgres_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/connector/status', methods=['GET'])
def get_connector_status():
    """Get Debezium connector status."""
    try:
        response = requests.get('http://localhost:8083/connectors/inventory-connector/status')
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cdc/events', methods=['GET'])
def get_cdc_events():
    """Get recent CDC events."""
    events = list(cdc_events_queue.queue)
    return jsonify(events)

@app.route('/api/mysql/customers', methods=['POST'])
def create_mysql_customer():
    """Create a new customer in MySQL."""
    try:
        data = request.json
        with mysql_engine.connect() as conn:
            query = text("""
                INSERT INTO customers (id, first_name, last_name, email)
                VALUES (:id, :first_name, :last_name, :email)
            """)
            conn.execute(query, data)
            conn.commit()
        return jsonify({'success': True, 'message': 'Customer created'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mysql/customers/<int:customer_id>', methods=['PUT'])
def update_mysql_customer(customer_id):
    """Update a customer in MySQL."""
    try:
        data = request.json
        with mysql_engine.connect() as conn:
            query = text("""
                UPDATE customers
                SET first_name = :first_name, last_name = :last_name, email = :email
                WHERE id = :id
            """)
            conn.execute(query, {**data, 'id': customer_id})
            conn.commit()
        return jsonify({'success': True, 'message': 'Customer updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mysql/customers/<int:customer_id>', methods=['DELETE'])
def delete_mysql_customer(customer_id):
    """Delete a customer from MySQL."""
    try:
        with mysql_engine.connect() as conn:
            query = text("DELETE FROM customers WHERE id = :id")
            conn.execute(query, {'id': customer_id})
            conn.commit()
        return jsonify({'success': True, 'message': 'Customer deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comparison', methods=['GET'])
def compare_databases():
    """Compare data between MySQL and PostgreSQL."""
    try:
        with mysql_engine.connect() as mysql_conn:
            mysql_result = mysql_conn.execute(text("SELECT id, first_name, last_name, email FROM customers ORDER BY id"))
            mysql_data = {row.id: dict(row._mapping) for row in mysql_result}

        with postgres_engine.connect() as pg_conn:
            pg_result = pg_conn.execute(text("SELECT id, first_name, last_name, email FROM customers ORDER BY id"))
            pg_data = {row.id: dict(row._mapping) for row in pg_result}

        # Find differences
        mysql_ids = set(mysql_data.keys())
        pg_ids = set(pg_data.keys())

        only_in_mysql = mysql_ids - pg_ids
        only_in_postgres = pg_ids - mysql_ids
        in_both = mysql_ids & pg_ids

        differences = []
        for id in in_both:
            if mysql_data[id] != pg_data[id]:
                differences.append({
                    'id': id,
                    'mysql': mysql_data[id],
                    'postgres': pg_data[id]
                })

        return jsonify({
            'only_in_mysql': list(only_in_mysql),
            'only_in_postgres': list(only_in_postgres),
            'differences': differences,
            'total_in_sync': len(in_both) - len(differences)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
