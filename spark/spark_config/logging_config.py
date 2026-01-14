"""
Logging configuration for Spark Streaming pipeline
Logs to both console and rotating files
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Log directory
LOG_DIR = Path("/opt/spark-data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log files
APP_LOG_FILE = LOG_DIR / "spark_streaming.log"
ERROR_LOG_FILE = LOG_DIR / "spark_errors.log"

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level=logging.INFO):
    """
    Configure logging with:
    - Console handler (for real-time monitoring)
    - Rotating file handler (for all logs)
    - Error file handler (for errors only)
    """
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # 1. Console Handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 2. Application Log File (rotating, keeps last 10 files of 10MB each)
    file_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 3. Error Log File (errors and critical only)
    error_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Log startup message
    logging.info("=" * 70)
    logging.info("Logging configured successfully")
    logging.info(f"Application logs: {APP_LOG_FILE}")
    logging.info(f"Error logs: {ERROR_LOG_FILE}")
    logging.info(f"Log level: {logging.getLevelName(log_level)}")
    logging.info("=" * 70)
    
    return root_logger


def log_batch_metrics(batch_id, record_count, processing_time_ms):
    """
    Log performance metrics for each batch
    """
    logger = logging.getLogger("BatchMetrics")
    
    logger.info(
        f"Batch {batch_id} | Records: {record_count} | "
        f"Processing Time: {processing_time_ms}ms | "
        f"Throughput: {record_count / (processing_time_ms / 1000):.2f} records/sec"
    )


def log_stream_progress(query):
    """
    Log streaming query progress
    """
    logger = logging.getLogger("StreamProgress")
    
    progress = query.lastProgress
    if progress:
        logger.info(
            f"Stream Progress | Batch: {progress['batchId']} | "
            f"Input Rows: {progress.get('numInputRows', 0)} | "
            f"Processed Rows/Sec: {progress.get('processedRowsPerSecond', 0):.2f}"
        )