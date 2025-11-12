import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Source Database Configuration
SOURCE_DB_CONFIG = {
    'host': os.getenv('SOURCE_DB_HOST', 'localhost'),
    'port': os.getenv('SOURCE_DB_PORT', '5432'),
    'database': os.getenv('SOURCE_DB_NAME', 'ecommerce_source'),
    'user': os.getenv('SOURCE_DB_USER', 'postgres'),
    'password': os.getenv('SOURCE_DB_PASSWORD', 'postgres')
}

# Warehouse Database Configuration
WAREHOUSE_DB_CONFIG = {
    'host': os.getenv('WAREHOUSE_DB_HOST', 'localhost'),
    'port': os.getenv('WAREHOUSE_DB_PORT', '5433'),
    'database': os.getenv('WAREHOUSE_DB_NAME', 'ecommerce_warehouse'),
    'user': os.getenv('WAREHOUSE_DB_USER', 'postgres'),
    'password': os.getenv('WAREHOUSE_DB_PASSWORD', 'postgres')
}

# Kafka Configuration
KAFKA_CONFIG = {
    'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    'group_id': 'etl-consumer-group-v3',  # Reset offset again
    'auto_offset_reset': 'earliest'
}

def get_source_engine():
    """Create SQLAlchemy engine for source database"""
    conn_string = (
        f"postgresql://{SOURCE_DB_CONFIG['user']}:{SOURCE_DB_CONFIG['password']}"
        f"@{SOURCE_DB_CONFIG['host']}:{SOURCE_DB_CONFIG['port']}/{SOURCE_DB_CONFIG['database']}"
    )
    return create_engine(conn_string)

def get_warehouse_engine():
    """Create SQLAlchemy engine for warehouse database"""
    conn_string = (
        f"postgresql://{WAREHOUSE_DB_CONFIG['user']}:{WAREHOUSE_DB_CONFIG['password']}"
        f"@{WAREHOUSE_DB_CONFIG['host']}:{WAREHOUSE_DB_CONFIG['port']}/{WAREHOUSE_DB_CONFIG['database']}"
    )
    return create_engine(conn_string)

def get_warehouse_session():
    """Create SQLAlchemy session for warehouse database"""
    engine = get_warehouse_engine()
    Session = sessionmaker(bind=engine)
    return Session()
