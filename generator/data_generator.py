"""
E-Commerce Event Data Generator
Writes Spark-safe CSV event files
"""

import csv
import random
import time
import logging
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    OUTPUT_DIR,
    EVENTS_PER_FILE,
    DELAY_BETWEEN_FILES,
    TOTAL_FILES,
    MAX_RETRIES,
    RETRY_DELAY,
)
from logging_config import setup_logging

logger = logging.getLogger(__name__)


# Sample data
PRODUCT_CATEGORIES = [
    "Electronics", "Clothing", "Home & Kitchen", "Books",
    "Sports & Outdoors", "Toys & Games", "Beauty", "Automotive"
]

PRODUCTS = {
    "Electronics": [
        ("Wireless Mouse", 29.99),
        ("USB-C Cable", 12.99),
        ("Bluetooth Speaker", 49.99),
        ("Laptop Stand", 34.99),
        ("Phone Case", 15.99),
    ],
    "Clothing": [
        ("Cotton T-Shirt", 19.99),
        ("Denim Jeans", 45.99),
        ("Running Shoes", 89.99),
        ("Winter Jacket", 129.99),
        ("Baseball Cap", 24.99),
    ],
    "Home & Kitchen": [
        ("Coffee Maker", 79.99),
        ("Dish Set", 45.99),
        ("Blender", 59.99),
        ("Bed Sheets", 39.99),
        ("Kitchen Knife Set", 69.99),
    ],
    "Books": [
        ("Python Programming", 34.99),
        ("Data Science Handbook", 42.99),
        ("Fiction Novel", 14.99),
        ("Cookbook", 24.99),
        ("Biography", 19.99),
    ],
    "Sports & Outdoors": [
        ("Yoga Mat", 29.99),
        ("Camping Tent", 149.99),
        ("Water Bottle", 19.99),
        ("Hiking Backpack", 79.99),
        ("Tennis Racket", 89.99),
    ],
    "Toys & Games": [
        ("Board Game", 34.99),
        ("LEGO Set", 59.99),
        ("Action Figure", 24.99),
        ("Puzzle", 19.99),
        ("Remote Control Car", 49.99),
    ],
    "Beauty": [
        ("Face Cream", 29.99),
        ("Shampoo", 12.99),
        ("Perfume", 79.99),
        ("Makeup Kit", 54.99),
        ("Hair Dryer", 44.99),
    ],
    "Automotive": [
        ("Car Phone Mount", 19.99),
        ("Dash Cam", 89.99),
        ("Car Vacuum", 39.99),
        ("Floor Mats", 34.99),
        ("Air Freshener", 9.99),
    ],
}

DEVICE_TYPES = ["mobile", "desktop", "tablet"]

CSV_FIELDS = [
    "user_id",
    "event_type",
    "product_id",
    "product_name",
    "product_category",
    "price",
    "event_timestamp",
    "session_id",
    "device_type",
]


# Event generation
def generate_event():
    category = random.choice(PRODUCT_CATEGORIES)
    product_name, price = random.choice(PRODUCTS[category])

    return {
        "user_id": f"user_{random.randint(1000, 9999)}",
        "event_type": random.choices(["view", "purchase"], weights=[85, 15])[0],
        "product_id": f"PROD_{random.randint(1000, 9999)}",
        "product_name": product_name,
        "product_category": category,
        "price": price,
        "event_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": f"session_{random.randint(100000, 999999)}",
        "device_type": random.choice(DEVICE_TYPES),
    }


# CSV writer (retry + rollback safe)
def create_csv_file(file_number):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_file = OUTPUT_DIR / f"events_{timestamp}_{file_number}.csv"
    temp_file = final_file.with_suffix(".csv.tmp")

    events = [generate_event() for _ in range(EVENTS_PER_FILE)]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with open(temp_file, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(events)

            temp_file.replace(final_file)

            logger.info(
                "File committed: %s | events=%d",
                final_file.name,
                len(events),
            )
            return

        except Exception as e:
            logger.error(
                "Write failed (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                str(e),
            )

            if temp_file.exists():
                temp_file.unlink()

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise


# Main generator loop
def run_generator():
    setup_logging()
    logger.info("Data generator started")

    file_count = 0

    try:
        while TOTAL_FILES == 0 or file_count < TOTAL_FILES:
            file_count += 1
            create_csv_file(file_count)

            if TOTAL_FILES == 0 or file_count < TOTAL_FILES:
                time.sleep(DELAY_BETWEEN_FILES)

    except KeyboardInterrupt:
        logger.warning("Generator stopped by user")

    except Exception as e:
        logger.critical("Fatal generator error: %s", str(e))
        raise
    logger.info("Data generator finished")