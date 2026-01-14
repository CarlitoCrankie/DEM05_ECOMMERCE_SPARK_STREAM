"""
Spark Structured Streaming Job
Reads CSV files from monitored folder and writes to PostgreSQL
With production-grade logging to files
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    DecimalType, TimestampType
)
import logging
import time

# Import our config modules
from spark_config.config import (
    INPUT_PATH, CHECKPOINT_PATH, LOG_PATH,
    POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_TABLE, POSTGRES_DRIVER,
    SPARK_APP_NAME, JDBC_JAR_PATH,
    MAX_FILES_PER_TRIGGER, PROCESSING_TIME_TRIGGER,
    ADAPTIVE_QUERY_EXECUTION, SHUFFLE_PARTITIONS, LOG_LEVEL
)
from spark_config.logging_config import (
    setup_logging, log_batch_metrics, log_stream_progress
)

# Set up logging
setup_logging(getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Define the schema for incoming CSV files
EVENT_SCHEMA = StructType([
    StructField("user_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("product_id", StringType(), False),
    StructField("product_name", StringType(), True),
    StructField("product_category", StringType(), True),
    StructField("price", DecimalType(10, 2), True),
    StructField("event_timestamp", TimestampType(), False),
    StructField("session_id", StringType(), True),
    StructField("device_type", StringType(), True),
])


def create_spark_session():
    """
    Create and configure Spark session with PostgreSQL support
    """
    logger.info("Creating Spark session...")
    
    spark = SparkSession.builder \
        .appName(SPARK_APP_NAME) \
        .config("spark.jars", JDBC_JAR_PATH) \
        .config("spark.sql.streaming.schemaInference", "false") \
        .config("spark.sql.adaptive.enabled", str(ADAPTIVE_QUERY_EXECUTION)) \
        .config("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS)) \
        .getOrCreate()
    
    # Set log level to reduce Spark's verbose output
    spark.sparkContext.setLogLevel("WARN")
    
    logger.info("Spark session created successfully")
    logger.info(f"Spark version: {spark.version}")
    logger.info(f"Application name: {SPARK_APP_NAME}")
    
    return spark


def read_stream(spark):
    """
    Set up streaming source to read CSV files
    """
    logger.info(f"Setting up stream reader for path: {INPUT_PATH}")
    
    stream_df = spark.readStream \
        .format("csv") \
        .option("header", "true") \
        .option("maxFilesPerTrigger", MAX_FILES_PER_TRIGGER) \
        .schema(EVENT_SCHEMA) \
        .load(INPUT_PATH)
    
    logger.info("Stream reader configured successfully")
    logger.debug(f"Schema: {stream_df.schema}")
    
    return stream_df


def transform_data(df):
    """
    Apply transformations to the streaming data
    """
    logger.info("Applying data transformations...")
    
    # Add processing timestamp
    transformed_df = df.withColumn("inserted_at", current_timestamp())
    
    # Data quality: Filter out null values in critical fields
    original_count = df.count() if df.isStreaming == False else "streaming"
    
    transformed_df = transformed_df.filter(
        (col("user_id").isNotNull()) & 
        (col("event_type").isNotNull()) &
        (col("product_id").isNotNull())
    )
    
    logger.info("Transformations applied successfully")
    logger.debug(f"Added inserted_at column and filtered null values")
    
    return transformed_df


def write_to_postgres(batch_df, batch_id):
    """
    Write each micro-batch to PostgreSQL with detailed logging
    """
    start_time = time.time()
    
    try:
        record_count = batch_df.count()
        
        if record_count == 0:
            logger.warning(f"Batch {batch_id} is empty, skipping write")
            return
        
        logger.info(f"Processing batch {batch_id} with {record_count} records")
        
        # Write to PostgreSQL
        batch_df.write \
            .format("jdbc") \
            .option("url", POSTGRES_URL) \
            .option("dbtable", POSTGRES_TABLE) \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("driver", POSTGRES_DRIVER) \
            .mode("append") \
            .save()
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Log success with metrics
        logger.info(f"✓ Batch {batch_id} written successfully to PostgreSQL")
        log_batch_metrics(batch_id, record_count, processing_time_ms)
        
        # Log sample of data for debugging
        logger.debug(f"Sample data from batch {batch_id}:")
        if record_count > 0:
            sample = batch_df.limit(2).collect()
            for row in sample:
                logger.debug(f"  {row.asDict()}")
        
    except Exception as e:
        logger.error(f"✗ Error writing batch {batch_id} to PostgreSQL")
        logger.error(f"Error details: {str(e)}", exc_info=True)
        raise


def start_streaming(spark, stream_df):
    """
    Start the streaming query with PostgreSQL sink
    """
    logger.info("Starting streaming query...")
    logger.info(f"Checkpoint location: {CHECKPOINT_PATH}")
    logger.info(f"Processing trigger: {PROCESSING_TIME_TRIGGER}")
    logger.info(f"Max files per trigger: {MAX_FILES_PER_TRIGGER}")
    
    query = stream_df.writeStream \
        .foreachBatch(write_to_postgres) \
        .option("checkpointLocation", CHECKPOINT_PATH) \
        .trigger(processingTime=PROCESSING_TIME_TRIGGER) \
        .start()
    

    logger.info("✓ Streaming query started successfully!")
    logger.info(f"Query ID: {query.id}")
    logger.info(f"Query name: {query.name if query.name else 'Unnamed'}")
    logger.info("Monitoring for new CSV files...")

    
    return query


def main():
    """
    Main function to orchestrate the streaming pipeline
    """

    logger.info("Starting E-Commerce Streaming Pipeline")    
    try:
        #  1: Create Spark session
        spark = create_spark_session()
        
        #  2: Read streaming data
        stream_df = read_stream(spark)
        
        #  3: Transform data
        transformed_df = transform_data(stream_df)
        
        #  4: Start streaming to PostgreSQL
        query = start_streaming(spark, transformed_df)
        
        #  5: Wait for termination
        logger.info("Pipeline is running. Press Ctrl+C to stop...")
        query.awaitTermination()
        
    except KeyboardInterrupt:
        logger.warning("Streaming stopped by user (Ctrl+C)")
        
    except Exception as e:
        logger.critical(f"Fatal error in streaming pipeline: {str(e)}", exc_info=True)
        raise
        
    finally:
        logger.info("Shutting down Spark session...")
        if 'spark' in locals():
            spark.stop()
        logger.info("Pipeline stopped successfully")


if __name__ == "__main__":
    main()