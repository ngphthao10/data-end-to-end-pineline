#!/usr/bin/env python3
"""
Basic CDC Consumer
Consumes Debezium CDC events from Kafka and replicates to PostgreSQL
"""

from kafka import KafkaConsumer
import json
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
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

# PostgreSQL connection
engine = create_engine('postgresql://postgres:mysecretpassword@localhost:5432/postgres')
metadata = MetaData()

# Define customers table
customers = Table('customers', metadata,
    Column('id', Integer, primary_key=True),
    Column('first_name', String(255)),
    Column('last_name', String(255)),
    Column('email', String(255))
)

print("Starting CDC consumer...")
print("Listening for changes on MySQL customers table...")

for message in consumer:
    try:
        data = message.value

        if data and 'payload' in data:
            payload = data['payload']
            operation = payload.get('op')

            if operation == 'c':  # Create
                after = payload.get('after')
                if after:
                    stmt = insert(customers).values(
                        id=after['id'],
                        first_name=after['first_name'],
                        last_name=after['last_name'],
                        email=after['email']
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['id'],
                        set_={
                            'first_name': after['first_name'],
                            'last_name': after['last_name'],
                            'email': after['email']
                        }
                    )
                    with engine.connect() as conn:
                        conn.execute(stmt)
                        conn.commit()
                    print(f"✓ INSERT: {after['first_name']} {after['last_name']}")

            elif operation == 'u':  # Update
                after = payload.get('after')
                if after:
                    stmt = insert(customers).values(
                        id=after['id'],
                        first_name=after['first_name'],
                        last_name=after['last_name'],
                        email=after['email']
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['id'],
                        set_={
                            'first_name': after['first_name'],
                            'last_name': after['last_name'],
                            'email': after['email']
                        }
                    )
                    with engine.connect() as conn:
                        conn.execute(stmt)
                        conn.commit()
                    print(f"✓ UPDATE: {after['first_name']} {after['last_name']}")

            elif operation == 'd':  # Delete
                before = payload.get('before')
                if before:
                    with engine.connect() as conn:
                        conn.execute(customers.delete().where(customers.c.id == before['id']))
                        conn.commit()
                    print(f"✓ DELETE: ID {before['id']}")

            elif operation == 'r':  # Read (initial snapshot)
                after = payload.get('after')
                if after:
                    stmt = insert(customers).values(
                        id=after['id'],
                        first_name=after['first_name'],
                        last_name=after['last_name'],
                        email=after['email']
                    )
                    stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
                    with engine.connect() as conn:
                        conn.execute(stmt)
                        conn.commit()
                    print(f"✓ SNAPSHOT: {after['first_name']} {after['last_name']}")

    except Exception as e:
        print(f"Error processing message: {e}")
