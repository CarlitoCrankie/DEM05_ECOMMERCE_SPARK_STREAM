"""
Spark Structured Streaming Job
Reads CSV files from monitored folder and writes to PostgreSQL
With enhanced validation and late data handling
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_timestamp, when, expr
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
        .option("mode", "PERMISSIVE") \
        .option("columnNameOfCorruptRecord", "_corrupt_record") \
        .schema(EVENT_SCHEMA) \
        .load(INPUT_PATH)
    
    logger.info("Stream reader configured successfully")
    logger.debug(f"Schema: {stream_df.schema}")
    
    return stream_df


def transform_data(df):
    """
    Apply transformations and validations to the streaming data
    """
    logger.info("Applying data transformations...")
    
    # Add processing timestamp for latency tracking
    transformed_df = df.withColumn("inserted_at", current_timestamp())
    
    # Enhanced validation: Filter out invalid records
    transformed_df = transformed_df.filter(
        # Required fields must not be null
        (col("user_id").isNotNull()) & 
        (col("event_type").isNotNull()) &
        (col("product_id").isNotNull()) &
        (col("event_timestamp").isNotNull()) &
        
        # user_id must not be empty string
        (col("user_id") != "") &
        
        # event_type must be valid
        (col("event_type").isin(["view", "purchase"])) &
        
        # price must be non-negative (if present)
        ((col("price").isNull()) | (col("price") >= 0)) &
        
        # device_type must be valid (if present)
        ((col("device_type").isNull()) | (col("device_type").isin(["mobile", "desktop", "tablet"]))) &
        
        # event_timestamp must be reasonable (not in future, not too old)
        (col("event_timestamp") <= current_timestamp()) &
        (col("event_timestamp") >= current_timestamp() - expr("INTERVAL 1 DAY"))
    )
    
    # Add data quality flag for records with missing optional fields
    transformed_df = transformed_df.withColumn(
        "data_quality_score",
        when(col("price").isNull(), 0.8)
        .when(col("product_name").isNull(), 0.9)
        .otherwise(1.0)
    )
    
    logger.info("Transformations applied successfully")
    logger.debug("Applied validations: null checks, value ranges, valid enums")
    
    return transformed_df


def write_to_postgres(batch_df, batch_id):
    """
    Write each micro-batch to PostgreSQL with detailed logging and error handling
    """
    start_time = time.time()
    
    try:
        record_count = batch_df.count()
        
        if record_count == 0:
            logger.warning(f"Batch {batch_id} is empty, skipping write")
            return
        
        logger.info(f"Processing batch {batch_id} with {record_count} records")
        
        # Log data quality metrics
        quality_metrics = batch_df.groupBy("data_quality_score").count().collect()
        for row in quality_metrics:
            logger.info(f"  Quality score {row['data_quality_score']}: {row['count']} records")
        
        # Drop data_quality_score before writing (not in PostgreSQL schema)
        batch_df_to_write = batch_df.drop("data_quality_score")
        
        # Write to PostgreSQL
        batch_df_to_write.write \
            .format("jdbc") \
            .option("url", POSTGRES_URL) \
            .option("dbtable", POSTGRES_TABLE) \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("driver", POSTGRES_DRIVER) \
            .option("batchsize", 1000) \
            .option("isolationLevel", "READ_COMMITTED") \
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
            sample = batch_df_to_write.limit(2).collect()
            for row in sample:
                logger.debug(f"  {row.asDict()}")
        
    except Exception as e:
        logger.error(f"✗ Error writing batch {batch_id} to PostgreSQL")
        logger.error(f"Error details: {str(e)}", exc_info=True)
        
        # Log failed batch details for debugging
        logger.error(f"Failed batch had {record_count if 'record_count' in locals() else 'unknown'} records")
        
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
        # Step 1: Create Spark session
        spark = create_spark_session()
        
        # Step 2: Read streaming data
        stream_df = read_stream(spark)
        
        # Step 3: Transform data with enhanced validations
        transformed_df = transform_data(stream_df)
        
        # Step 4: Start streaming to PostgreSQL
        query = start_streaming(spark, transformed_df)
        
        # Step 5: Wait for termination
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
