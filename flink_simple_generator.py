#!/usr/bin/env python3
"""
Flink-style Data Stream Generator for CDC Demo
Generates continuous INSERT, UPDATE, DELETE operations
"""

import pymysql
import random
import time
from datetime import datetime
from faker import Faker

MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'mysqluser',
    'password': 'mysqlpw',
    'database': 'inventory'
}

class DataStreamGenerator:
    def __init__(self):
        self.fake = Faker()
        self.conn = None
        self.operations_count = {'INSERT': 0, 'UPDATE': 0, 'DELETE': 0}

    def connect(self):
        self.conn = pymysql.connect(**MYSQL_CONFIG)
        print("✓ Connected to MySQL")

    def get_customer_ids(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id FROM customers")
            return [row[0] for row in cursor.fetchall()]

    def get_next_id(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM customers")
            max_id = cursor.fetchone()[0]
            return (max_id + 1) if max_id else 2001

    def generate_insert(self):
        try:
            customer_id = self.get_next_id()
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}@{self.fake.free_email_domain()}"

            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO customers (id, first_name, last_name, email) VALUES (%s, %s, %s, %s)",
                    (customer_id, first_name, last_name, email)
                )
            self.conn.commit()
            self.operations_count['INSERT'] += 1
            return True, f"INSERT id={customer_id}, {first_name} {last_name}"
        except Exception as e:
            self.conn.rollback()
            return False, f"INSERT failed: {e}"

    def generate_update(self):
        try:
            customer_ids = self.get_customer_ids()
            if not customer_ids:
                return False, "No customers to update"

            customer_id = random.choice(customer_ids)
            update_field = random.choice(['first_name', 'last_name', 'email'])

            if update_field == 'first_name':
                new_value = self.fake.first_name()
                sql = "UPDATE customers SET first_name = %s WHERE id = %s"
            elif update_field == 'last_name':
                new_value = self.fake.last_name()
                sql = "UPDATE customers SET last_name = %s WHERE id = %s"
            else:
                new_value = self.fake.email()
                sql = "UPDATE customers SET email = %s WHERE id = %s"

            with self.conn.cursor() as cursor:
                cursor.execute(sql, (new_value, customer_id))
            self.conn.commit()
            self.operations_count['UPDATE'] += 1
            return True, f"UPDATE id={customer_id}, {update_field}={new_value}"
        except Exception as e:
            self.conn.rollback()
            return False, f"UPDATE failed: {e}"

    def generate_delete(self):
        try:
            customer_ids = self.get_customer_ids()
            if len(customer_ids) < 50:
                return False, "Minimum dataset threshold (50 customers)"

            customer_id = random.choice(customer_ids)

            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
            self.conn.commit()
            self.operations_count['DELETE'] += 1
            return True, f"DELETE id={customer_id}"
        except Exception as e:
            self.conn.rollback()
            return False, f"DELETE failed: {e}"

    def run_stream(self, rate_per_second=2, insert_ratio=0.5, update_ratio=0.3, delete_ratio=0.2):
        print("\n" + "="*70)
        print("  Flink-style Data Stream Generator")
        print("="*70)
        print(f"  Rate: {rate_per_second} operations/second")
        print(f"  Distribution: INSERT={insert_ratio*100}%, UPDATE={update_ratio*100}%, DELETE={delete_ratio*100}%")
        print("="*70 + "\n")

        self.connect()

        delay = 1.0 / rate_per_second
        operations = ['INSERT', 'UPDATE', 'DELETE']
        weights = [insert_ratio, update_ratio, delete_ratio]

        try:
            while True:
                operation = random.choices(operations, weights=weights)[0]

                if operation == 'INSERT':
                    success, msg = self.generate_insert()
                    icon = "➕"
                elif operation == 'UPDATE':
                    success, msg = self.generate_update()
                    icon = "✏️ "
                else:
                    success, msg = self.generate_delete()
                    icon = "🗑️ "

                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                status = "✓" if success else "✗"
                print(f"[{timestamp}] {status} {icon} {operation:6s} | {msg}")

                if sum(self.operations_count.values()) % 20 == 0:
                    self.print_statistics()

                time.sleep(delay)

        except KeyboardInterrupt:
            print("\n" + "="*70)
            print("  Stream generation stopped")
            self.print_statistics()
            print("="*70)
        finally:
            if self.conn:
                self.conn.close()

    def print_statistics(self):
        total = sum(self.operations_count.values())
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM customers")
            count = cursor.fetchone()[0]

        print("\n" + "-"*70)
        print(f"  Statistics | Total Operations: {total} | Customers: {count}")
        print(f"  INSERT: {self.operations_count['INSERT']:4d} | "
              f"UPDATE: {self.operations_count['UPDATE']:4d} | "
              f"DELETE: {self.operations_count['DELETE']:4d}")
        print("-"*70 + "\n")


def main():
    generator = DataStreamGenerator()

    RATE_PER_SECOND = 2
    INSERT_RATIO = 0.5
    UPDATE_RATIO = 0.3
    DELETE_RATIO = 0.2

    print("\n🚀 Starting Flink-style Data Stream Generator")
    print("📊 This simulates Apache Flink DataStream operations")
    print("🎯 Target: MySQL → Debezium → Kafka → PostgreSQL")
    print("\n⏹️  Press Ctrl+C to stop\n")

    generator.run_stream(
        rate_per_second=RATE_PER_SECOND,
        insert_ratio=INSERT_RATIO,
        update_ratio=UPDATE_RATIO,
        delete_ratio=DELETE_RATIO
    )


if __name__ == "__main__":
    try:
        import pymysql
        from faker import Faker
    except ImportError:
        print("❌ ERROR: Missing dependencies")
        print("📦 Install with: pip install pymysql faker")
        exit(1)

    main()
