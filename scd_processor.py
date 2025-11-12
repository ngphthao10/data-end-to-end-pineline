from datetime import datetime
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SCDProcessor:
    """Handles SCD Type 1 and Type 2 processing for dimension tables"""

    def __init__(self, warehouse_engine):
        self.engine = warehouse_engine

    def process_customer_scd2(self, customer_data, operation='c'):
        """
        Process customer changes using SCD Type 2

        Args:
            customer_data: Dictionary containing customer information
            operation: 'c' (create), 'u' (update), 'd' (delete)
        """
        with self.engine.connect() as conn:
            customer_id = customer_data.get('customer_id')

            if operation == 'd':
                # Handle delete: end-date current record
                conn.execute(
                    text("""
                        UPDATE dim_customer
                        SET valid_to = :now, is_current = FALSE
                        WHERE customer_id = :customer_id AND is_current = TRUE
                    """),
                    {'now': datetime.now(), 'customer_id': customer_id}
                )
                conn.commit()
                logger.info(f"Customer {customer_id} deleted (end-dated)")
                return

            # Check if customer exists and get current record
            current_record = conn.execute(
                text("""
                    SELECT customer_key, first_name, last_name, email, phone,
                           address, city, country, version
                    FROM dim_customer
                    WHERE customer_id = :customer_id AND is_current = TRUE
                """),
                {'customer_id': customer_id}
            ).fetchone()

            if operation == 'c' or current_record is None:
                # Insert new customer (create)
                conn.execute(
                    text("""
                        INSERT INTO dim_customer (
                            customer_id, first_name, last_name, email, phone,
                            address, city, country, valid_from, is_current, version
                        ) VALUES (
                            :customer_id, :first_name, :last_name, :email, :phone,
                            :address, :city, :country, :valid_from, TRUE, 1
                        )
                    """),
                    {
                        'customer_id': customer_id,
                        'first_name': customer_data.get('first_name'),
                        'last_name': customer_data.get('last_name'),
                        'email': customer_data.get('email'),
                        'phone': customer_data.get('phone'),
                        'address': customer_data.get('address'),
                        'city': customer_data.get('city'),
                        'country': customer_data.get('country'),
                        'valid_from': datetime.now()
                    }
                )
                conn.commit()
                logger.info(f"New customer {customer_id} inserted")

            elif operation == 'u':
                # Check if any SCD Type 2 attributes changed
                changed = (
                    current_record[4] != customer_data.get('phone') or
                    current_record[5] != customer_data.get('address') or
                    current_record[6] != customer_data.get('city') or
                    current_record[7] != customer_data.get('country')
                )

                if changed:
                    # End-date current record
                    conn.execute(
                        text("""
                            UPDATE dim_customer
                            SET valid_to = :now, is_current = FALSE
                            WHERE customer_id = :customer_id AND is_current = TRUE
                        """),
                        {'now': datetime.now(), 'customer_id': customer_id}
                    )

                    # Insert new version
                    new_version = current_record[8] + 1
                    conn.execute(
                        text("""
                            INSERT INTO dim_customer (
                                customer_id, first_name, last_name, email, phone,
                                address, city, country, valid_from, is_current, version
                            ) VALUES (
                                :customer_id, :first_name, :last_name, :email, :phone,
                                :address, :city, :country, :valid_from, TRUE, :version
                            )
                        """),
                        {
                            'customer_id': customer_id,
                            'first_name': customer_data.get('first_name'),
                            'last_name': customer_data.get('last_name'),
                            'email': customer_data.get('email'),
                            'phone': customer_data.get('phone'),
                            'address': customer_data.get('address'),
                            'city': customer_data.get('city'),
                            'country': customer_data.get('country'),
                            'valid_from': datetime.now(),
                            'version': new_version
                        }
                    )
                    conn.commit()
                    logger.info(f"Customer {customer_id} updated (new version {new_version})")
                else:
                    # No relevant changes, just update Type 1 attributes
                    conn.execute(
                        text("""
                            UPDATE dim_customer
                            SET first_name = :first_name,
                                last_name = :last_name,
                                email = :email
                            WHERE customer_id = :customer_id AND is_current = TRUE
                        """),
                        {
                            'customer_id': customer_id,
                            'first_name': customer_data.get('first_name'),
                            'last_name': customer_data.get('last_name'),
                            'email': customer_data.get('email')
                        }
                    )
                    conn.commit()
                    logger.info(f"Customer {customer_id} updated (no new version)")

    def process_product_scd2(self, product_data, operation='c'):
        """
        Process product changes using SCD Type 2

        Args:
            product_data: Dictionary containing product information
            operation: 'c' (create), 'u' (update), 'd' (delete)
        """
        with self.engine.connect() as conn:
            product_id = product_data.get('product_id')

            if operation == 'd':
                # Handle delete: end-date current record
                conn.execute(
                    text("""
                        UPDATE dim_product
                        SET valid_to = :now, is_current = FALSE
                        WHERE product_id = :product_id AND is_current = TRUE
                    """),
                    {'now': datetime.now(), 'product_id': product_id}
                )
                conn.commit()
                logger.info(f"Product {product_id} deleted (end-dated)")
                return

            # Calculate margin percentage
            price = float(product_data.get('price', 0))
            cost = float(product_data.get('cost', 0))
            margin = ((price - cost) / price * 100) if price > 0 else 0

            # Check if product exists
            current_record = conn.execute(
                text("""
                    SELECT product_key, product_name, category, brand, price,
                           cost, version
                    FROM dim_product
                    WHERE product_id = :product_id AND is_current = TRUE
                """),
                {'product_id': product_id}
            ).fetchone()

            if operation == 'c' or current_record is None:
                # Insert new product
                conn.execute(
                    text("""
                        INSERT INTO dim_product (
                            product_id, product_name, category, brand, price, cost,
                            margin_percentage, description, valid_from, is_current, version
                        ) VALUES (
                            :product_id, :product_name, :category, :brand, :price, :cost,
                            :margin_percentage, :description, :valid_from, TRUE, 1
                        )
                    """),
                    {
                        'product_id': product_id,
                        'product_name': product_data.get('product_name'),
                        'category': product_data.get('category'),
                        'brand': product_data.get('brand'),
                        'price': price,
                        'cost': cost,
                        'margin_percentage': margin,
                        'description': product_data.get('description'),
                        'valid_from': datetime.now()
                    }
                )
                conn.commit()
                logger.info(f"New product {product_id} inserted")

            elif operation == 'u':
                # Check if price or cost changed (SCD Type 2 attributes)
                changed = (
                    float(current_record[4]) != price or
                    float(current_record[5]) != cost
                )

                if changed:
                    # End-date current record
                    conn.execute(
                        text("""
                            UPDATE dim_product
                            SET valid_to = :now, is_current = FALSE
                            WHERE product_id = :product_id AND is_current = TRUE
                        """),
                        {'now': datetime.now(), 'product_id': product_id}
                    )

                    # Insert new version
                    new_version = current_record[6] + 1
                    conn.execute(
                        text("""
                            INSERT INTO dim_product (
                                product_id, product_name, category, brand, price, cost,
                                margin_percentage, description, valid_from, is_current, version
                            ) VALUES (
                                :product_id, :product_name, :category, :brand, :price, :cost,
                                :margin_percentage, :description, :valid_from, TRUE, :version
                            )
                        """),
                        {
                            'product_id': product_id,
                            'product_name': product_data.get('product_name'),
                            'category': product_data.get('category'),
                            'brand': product_data.get('brand'),
                            'price': price,
                            'cost': cost,
                            'margin_percentage': margin,
                            'description': product_data.get('description'),
                            'valid_from': datetime.now(),
                            'version': new_version
                        }
                    )
                    conn.commit()
                    logger.info(f"Product {product_id} updated (new version {new_version})")
                else:
                    # Update Type 1 attributes only
                    conn.execute(
                        text("""
                            UPDATE dim_product
                            SET product_name = :product_name,
                                category = :category,
                                brand = :brand,
                                description = :description
                            WHERE product_id = :product_id AND is_current = TRUE
                        """),
                        {
                            'product_id': product_id,
                            'product_name': product_data.get('product_name'),
                            'category': product_data.get('category'),
                            'brand': product_data.get('brand'),
                            'description': product_data.get('description')
                        }
                    )
                    conn.commit()
                    logger.info(f"Product {product_id} updated (no new version)")

    def get_current_customer_key(self, customer_id):
        """Get current customer_key for a given customer_id"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT customer_key
                    FROM dim_customer
                    WHERE customer_id = :customer_id AND is_current = TRUE
                """),
                {'customer_id': customer_id}
            ).fetchone()
            return result[0] if result else None

    def get_current_product_key(self, product_id):
        """Get current product_key for a given product_id"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT product_key
                    FROM dim_product
                    WHERE product_id = :product_id AND is_current = TRUE
                """),
                {'product_id': product_id}
            ).fetchone()
            return result[0] if result else None

    def get_date_key(self, date_value):
        """Convert date to date_key (YYYYMMDD format)"""
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        return int(date_value.strftime('%Y%m%d'))
