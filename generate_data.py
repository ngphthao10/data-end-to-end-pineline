"""
Generate sample e-commerce data for testing
Modes:
- initial: Generate initial dataset once
- continuous: Continuously generate new data and make changes (for CDC demo)
"""
from faker import Faker
from db_config import get_source_engine
from sqlalchemy import text
import random
from datetime import datetime, timedelta
import logging
import time
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

fake = Faker()


def generate_customers(engine, num_customers=1000):
    """Generate fake customer data"""
    logger.info(f"Generating {num_customers} customers...")

    # Check existing customers count
    with engine.connect() as conn:
        existing_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        if existing_count >= num_customers:
            logger.info(f"✓ Already have {existing_count} customers, skipping generation")
            return

        start_idx = existing_count
        customers_to_create = num_customers - existing_count
        logger.info(f"  Creating {customers_to_create} more customers (starting from {start_idx})")

        for i in range(customers_to_create):
            # Generate unique email with index to avoid collisions
            email = f"customer{start_idx + i}_{fake.user_name()}@example.com"

            try:
                conn.execute(
                    text("""
                        INSERT INTO customers (
                            first_name, last_name, email, phone, address, city, country
                        ) VALUES (
                            :first_name, :last_name, :email, :phone, :address, :city, :country
                        )
                    """),
                    {
                        'first_name': fake.first_name(),
                        'last_name': fake.last_name(),
                        'email': email,
                        'phone': fake.phone_number()[:20],
                        'address': fake.street_address(),
                        'city': fake.city(),
                        'country': fake.country()
                    }
                )

                if (i + 1) % 100 == 0:
                    conn.commit()
                    logger.info(f"  Created {start_idx + i + 1} customers")

            except Exception as e:
                logger.warning(f"  Skipping duplicate: {e}")
                continue

        conn.commit()

    # Final count
    with engine.connect() as conn:
        final_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        logger.info(f"✓ Total customers in database: {final_count}")


def generate_products(engine, num_products=500):
    """Generate fake product data"""
    logger.info(f"Generating {num_products} products...")

    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys', 'Food']
    brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE', 'Generic']

    with engine.connect() as conn:
        # Check existing products
        existing_count = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
        if existing_count >= num_products:
            logger.info(f"✓ Already have {existing_count} products, skipping generation")
            return

        products_to_create = num_products - existing_count
        logger.info(f"  Creating {products_to_create} more products")

        for i in range(products_to_create):
            price = round(random.uniform(10, 1000), 2)
            cost = round(price * random.uniform(0.4, 0.7), 2)

            conn.execute(
                text("""
                    INSERT INTO products (
                        product_name, category, brand, price, cost, description
                    ) VALUES (
                        :product_name, :category, :brand, :price, :cost, :description
                    )
                """),
                {
                    'product_name': fake.catch_phrase(),
                    'category': random.choice(categories),
                    'brand': random.choice(brands),
                    'price': price,
                    'cost': cost,
                    'description': fake.text(max_nb_chars=200)
                }
            )

            if (i + 1) % 100 == 0:
                conn.commit()
                logger.info(f"  Created {existing_count + i + 1} products")

        conn.commit()

    with engine.connect() as conn:
        final_count = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
        logger.info(f"✓ Total products in database: {final_count}")


def generate_orders(engine, num_orders=5000):
    """Generate fake orders and order items"""
    logger.info(f"Generating {num_orders} orders...")

    statuses = ['pending', 'processing', 'shipped', 'delivered']

    with engine.connect() as conn:
        # Check existing orders
        existing_count = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        if existing_count >= num_orders:
            logger.info(f"✓ Already have {existing_count} orders, skipping generation")
            return

        orders_to_create = num_orders - existing_count
        logger.info(f"  Creating {orders_to_create} more orders")

        # Get customer and product IDs
        customers = conn.execute(text("SELECT customer_id FROM customers")).fetchall()
        products = conn.execute(text("SELECT product_id, price FROM products")).fetchall()

        if not customers or not products:
            logger.error("No customers or products found. Generate them first.")
            return

        customer_ids = [c[0] for c in customers]
        product_list = [(p[0], float(p[1])) for p in products]

        for i in range(orders_to_create):
            # Random order date in last 180 days
            order_date = datetime.now() - timedelta(days=random.randint(0, 180))
            customer_id = random.choice(customer_ids)
            status = random.choice(statuses)

            # Insert order
            result = conn.execute(
                text("""
                    INSERT INTO orders (customer_id, order_date, status, total_amount)
                    VALUES (:customer_id, :order_date, :status, 0)
                    RETURNING order_id
                """),
                {
                    'customer_id': customer_id,
                    'order_date': order_date,
                    'status': status
                }
            )
            order_id = result.fetchone()[0]

            # Generate 1-5 order items per order
            num_items = random.randint(1, 5)
            total_amount = 0

            for _ in range(num_items):
                product_id, price = random.choice(product_list)
                quantity = random.randint(1, 3)
                unit_price = price
                line_total = round(quantity * unit_price, 2)
                total_amount += line_total

                conn.execute(
                    text("""
                        INSERT INTO order_items (
                            order_id, product_id, quantity, unit_price, line_total
                        ) VALUES (
                            :order_id, :product_id, :quantity, :unit_price, :line_total
                        )
                    """),
                    {
                        'order_id': order_id,
                        'product_id': product_id,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'line_total': line_total
                    }
                )

            # Update order total
            conn.execute(
                text("UPDATE orders SET total_amount = :total WHERE order_id = :order_id"),
                {'total': total_amount, 'order_id': order_id}
            )

            if (i + 1) % 100 == 0:
                conn.commit()
                logger.info(f"  Created {existing_count + i + 1} orders")

        conn.commit()

    with engine.connect() as conn:
        final_count = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        logger.info(f"✓ Total orders in database: {final_count}")


def print_statistics(engine):
    """Print current database statistics"""
    with engine.connect() as conn:
        customers = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        products = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
        orders = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        order_items = conn.execute(text("SELECT COUNT(*) FROM order_items")).scalar()

        logger.info("\n--- Database Statistics ---")
        logger.info(f"Customers: {customers}")
        logger.info(f"Products: {products}")
        logger.info(f"Orders: {orders}")
        logger.info(f"Order Items: {order_items}")


def update_random_customer(engine):
    """Update a random customer's information (for SCD Type 2 demo)"""
    with engine.connect() as conn:
        # Get a random customer
        result = conn.execute(
            text("SELECT customer_id, first_name, last_name FROM customers ORDER BY RANDOM() LIMIT 1")
        ).fetchone()

        if not result:
            return

        customer_id = result[0]

        # Update with new address/city/country
        new_city = fake.city()
        new_country = fake.country()
        new_address = fake.street_address()

        conn.execute(
            text("""
                UPDATE customers
                SET city = :city, country = :country, address = :address
                WHERE customer_id = :customer_id
            """),
            {
                'customer_id': customer_id,
                'city': new_city,
                'country': new_country,
                'address': new_address
            }
        )
        conn.commit()
        logger.info(f"✓ Updated customer #{customer_id} - New location: {new_city}, {new_country}")


def update_random_product_price(engine):
    """Update a random product's price (for SCD Type 2 demo)"""
    with engine.connect() as conn:
        # Get a random product
        result = conn.execute(
            text("SELECT product_id, product_name, price FROM products ORDER BY RANDOM() LIMIT 1")
        ).fetchone()

        if not result:
            return

        product_id, product_name, old_price = result[0], result[1], float(result[2])

        # Change price by -20% to +30%
        price_change = random.uniform(-0.2, 0.3)
        new_price = round(old_price * (1 + price_change), 2)
        new_cost = round(new_price * random.uniform(0.4, 0.7), 2)

        conn.execute(
            text("""
                UPDATE products
                SET price = :price, cost = :cost
                WHERE product_id = :product_id
            """),
            {
                'product_id': product_id,
                'price': new_price,
                'cost': new_cost
            }
        )
        conn.commit()
        logger.info(f"✓ Updated product #{product_id} '{product_name}' - Price: ${old_price} → ${new_price}")


def create_new_order(engine):
    """Create a new order with random items"""
    with engine.connect() as conn:
        # Get random customer and products
        customer_result = conn.execute(
            text("SELECT customer_id FROM customers ORDER BY RANDOM() LIMIT 1")
        ).fetchone()

        products = conn.execute(
            text("SELECT product_id, price FROM products ORDER BY RANDOM() LIMIT 5")
        ).fetchall()

        if not customer_result or not products:
            return

        customer_id = customer_result[0]
        order_date = datetime.now()
        status = random.choice(['pending', 'processing', 'shipped', 'delivered'])

        # Insert order
        result = conn.execute(
            text("""
                INSERT INTO orders (customer_id, order_date, status, total_amount)
                VALUES (:customer_id, :order_date, :status, 0)
                RETURNING order_id
            """),
            {
                'customer_id': customer_id,
                'order_date': order_date,
                'status': status
            }
        )
        order_id = result.fetchone()[0]

        # Add 1-3 items to the order
        num_items = random.randint(1, 3)
        total_amount = 0

        for i in range(num_items):
            product_id, price = products[i][0], float(products[i][1])
            quantity = random.randint(1, 3)
            unit_price = price
            line_total = round(quantity * unit_price, 2)
            total_amount += line_total

            conn.execute(
                text("""
                    INSERT INTO order_items (
                        order_id, product_id, quantity, unit_price, line_total
                    ) VALUES (
                        :order_id, :product_id, :quantity, :unit_price, :line_total
                    )
                """),
                {
                    'order_id': order_id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'line_total': line_total
                }
            )

        # Update order total
        conn.execute(
            text("UPDATE orders SET total_amount = :total WHERE order_id = :order_id"),
            {'total': total_amount, 'order_id': order_id}
        )

        conn.commit()
        logger.info(f"✓ Created new order #{order_id} - Customer #{customer_id} - Total: ${total_amount:.2f}")


def create_new_customer(engine):
    """Create a new customer"""
    with engine.connect() as conn:
        email = f"customer_{fake.user_name()}_{random.randint(1000, 9999)}@example.com"

        try:
            conn.execute(
                text("""
                    INSERT INTO customers (
                        first_name, last_name, email, phone, address, city, country
                    ) VALUES (
                        :first_name, :last_name, :email, :phone, :address, :city, :country
                    )
                """),
                {
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'email': email,
                    'phone': fake.phone_number()[:20],
                    'address': fake.street_address(),
                    'city': fake.city(),
                    'country': fake.country()
                }
            )
            conn.commit()
            logger.info(f"✓ Created new customer - {email}")
        except Exception as e:
            logger.warning(f"Failed to create customer: {e}")


def continuous_mode(engine, interval=5):
    """
    Continuously generate data changes for CDC demo

    Args:
        engine: Database engine
        interval: Seconds between operations (default: 5)
    """
    logger.info("=" * 60)
    logger.info("CONTINUOUS DATA GENERATION MODE")
    logger.info(f"Interval: {interval} seconds")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    operations = [
        ('Update Customer', update_random_customer, 0.3),      # 30% chance
        ('Update Product Price', update_random_product_price, 0.3),  # 30% chance
        ('Create New Order', create_new_order, 0.3),           # 30% chance
        ('Create New Customer', create_new_customer, 0.1),     # 10% chance
    ]

    counter = 0

    try:
        while True:
            counter += 1
            logger.info(f"\n[Iteration #{counter}]")

            # Random operation based on weights
            rand = random.random()
            cumulative = 0

            for op_name, op_func, weight in operations:
                cumulative += weight
                if rand < cumulative:
                    try:
                        op_func(engine)
                    except Exception as e:
                        logger.error(f"Error in {op_name}: {e}")
                    break

            # Wait before next operation
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("\n\n✓ Stopped continuous generation")


def initial_mode(engine):
    """Generate initial dataset once"""
    logger.info("=" * 60)
    logger.info("INITIAL DATA GENERATION MODE")
    logger.info("=" * 60)

    generate_customers(engine, num_customers=1000)
    generate_products(engine, num_products=500)
    generate_orders(engine, num_orders=5000)

    logger.info("✓ Initial data generation completed!")
    print_statistics(engine)


def main():
    """Main function with mode selection"""
    # Parse command line arguments
    mode = 'continuous' if len(sys.argv) > 1 and sys.argv[1] == 'continuous' else 'initial'
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    engine = get_source_engine()

    if mode == 'continuous':
        continuous_mode(engine, interval)
    else:
        initial_mode(engine)


if __name__ == '__main__':
    # Print usage
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage:")
        print("  python generate_data.py                    # Initial mode - generate data once")
        print("  python generate_data.py continuous [interval]  # Continuous mode - generate data continuously")
        print("")
        print("Examples:")
        print("  python generate_data.py                    # Generate initial dataset")
        print("  python generate_data.py continuous         # Continuous mode (5 sec interval)")
        print("  python generate_data.py continuous 3       # Continuous mode (3 sec interval)")
        sys.exit(0)

    main()
