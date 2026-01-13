from pathlib import Path

# Output Configuration
OUTPUT_DIR = Path("/opt/spark-data/input") # Inside Docker container

# Data Generation Settings
EVENTS_PER_FILE = 10
DELAY_BETWEEN_FILES = 5 # seconds
TOTAL_FILES = 20  # 0 = infinite

# Retry Settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds