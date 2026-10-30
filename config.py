import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from sqlalchemy import URL, create_engine

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = PROJECT_DIR / "data" / "food_orders.csv"
CSV_PATH = Path(os.getenv("FOOD_ORDERS_CSV", str(DEFAULT_CSV_PATH if DEFAULT_CSV_PATH.exists() else r"D:\ETL\food_orders.csv")))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
RAW_DATABASE = "food_orders_raw_db"
ANALYTICS_DATABASE = "food_orders_analytics_db"
RAW_TABLE = "raw_food_orders"
CLEAN_TABLE = "cleaned_food_orders"
RAW_COLUMNS = ["Order ID", "Customer ID", "Restaurant ID", "Order Date and Time", "Delivery Date and Time", "Order Value", "Delivery Fee", "Payment Method", "Discounts and Offers", "Commission Fee", "Payment Processing Fee", "Refunds/Chargebacks", "Weather Condition", "Order Channel"]


def make_engine(database=None):
    if not MYSQL_PASSWORD:
        raise RuntimeError("MYSQL_PASSWORD is not set. Copy .env.example to .env and configure it.")
    url = URL.create("mysql+pymysql", username=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST, port=MYSQL_PORT, database=database)
    return create_engine(url, pool_pre_ping=True, future=True)


def ensure_databases():
    if not MYSQL_PASSWORD:
        raise RuntimeError("Set MYSQL_PASSWORD in the project .env file first.")
    url = URL.create("mysql+pymysql", username=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST, port=MYSQL_PORT)
    engine = create_engine(url, pool_pre_ping=True, future=True)
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE DATABASE IF NOT EXISTS food_orders_raw_db CHARACTER SET utf8mb4")
            conn.exec_driver_sql("CREATE DATABASE IF NOT EXISTS food_orders_analytics_db CHARACTER SET utf8mb4")
    finally:
        engine.dispose()
