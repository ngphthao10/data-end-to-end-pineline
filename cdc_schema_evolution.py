#!/usr/bin/env python3
"""
CDC Consumer with Schema Evolution Support
Consumes Debezium CDC events from Kafka and replicates to PostgreSQL
"""

from kafka import KafkaConsumer
import json
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.dialects.postgresql import insert

# Kafka consumer
consumer = KafkaConsumer(
    'dbserver1.inventory.customers',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='cdc-consumer-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x is not None else None
)

# PostgreSQL engine
pg_engine = create_engine('postgresql://postgres:mysecretpassword@localhost:5432/postgres')

def get_pg_columns():
    """Get current PostgreSQL table columns dynamically"""
    inspector = inspect(pg_engine)
    columns = [col['name'] for col in inspector.get_columns('customers')]
    return set(columns)

def filter_fields(data, pg_columns):
    """Filter data fields to only include columns that exist in PostgreSQL"""
    return {k: v for k, v in data.items() if k in pg_columns}

print("Starting CDC consumer with schema evolution support...")
print("Listening for changes on MySQL customers table...")

for message in consumer:
    try:
        data = message.value
        if not data or 'payload' not in data:
            continue

        payload = data['payload']
        operation = payload.get('op')

        # Get current PostgreSQL columns
        pg_columns = get_pg_columns()

        if operation in ('r', 'c'):  # Read (snapshot) or Create
            after = payload.get('after')
            if after:
                filtered_data = filter_fields(after, pg_columns)

                with pg_engine.connect() as conn:
                    stmt = text(f"""
                        INSERT INTO customers ({', '.join(filtered_data.keys())})
                        VALUES ({', '.join([f':{k}' for k in filtered_data.keys()])})
                        ON CONFLICT (id) DO UPDATE SET
                        {', '.join([f'{k}=EXCLUDED.{k}' for k in filtered_data.keys() if k != 'id'])}
                    """)
                    conn.execute(stmt, filtered_data)
                    conn.commit()

                op_name = "SNAPSHOT" if operation == 'r' else "INSERT"
                print(f"✓ {op_name}: {after.get('first_name')} {after.get('last_name')}")

        elif operation == 'u':  # Update
            after = payload.get('after')
            if after:
                filtered_data = filter_fields(after, pg_columns)

                with pg_engine.connect() as conn:
                    stmt = text(f"""
                        INSERT INTO customers ({', '.join(filtered_data.keys())})
                        VALUES ({', '.join([f':{k}' for k in filtered_data.keys()])})
                        ON CONFLICT (id) DO UPDATE SET
                        {', '.join([f'{k}=EXCLUDED.{k}' for k in filtered_data.keys() if k != 'id'])}
                    """)
                    conn.execute(stmt, filtered_data)
                    conn.commit()

                print(f"✓ UPDATE: {after.get('first_name')} {after.get('last_name')}")

        elif operation == 'd':  # Delete
            before = payload.get('before')
            if before:
                with pg_engine.connect() as conn:
                    conn.execute(text("DELETE FROM customers WHERE id = :id"), {"id": before['id']})
                    conn.commit()
                print(f"✓ DELETE: ID {before['id']}")

    except Exception as e:
        print(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
