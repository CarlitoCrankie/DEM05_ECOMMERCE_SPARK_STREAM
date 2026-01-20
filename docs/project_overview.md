# Project Overview: Real-Time E-Commerce Event Pipeline

## Purpose

This pipeline ingests simulated e-commerce user events (product views and purchases), processes them using Apache Spark Structured Streaming, and stores them in PostgreSQL for analysis.

## Components

### Data Generator (`data_generator.py`)
- Produces CSV files containing fake e-commerce events
- Each event includes: user_id, event_type, product_id, product_name, category, price, timestamp, session_id, device_type
- Writes files atomically using a temp-file-then-rename pattern to prevent Spark from reading partial files
- Configurable output rate and batch size via `config.py`

### Spark Streaming Job (`spark_streaming_to_postgres.py`)
- Monitors the input directory for new CSV files
- Reads files using a predefined schema (no inference)
- Applies transformations:
  - Adds `inserted_at` timestamp
  - Filters records with null values in required fields (user_id, event_type, product_id)
- Writes each micro-batch to PostgreSQL using JDBC
- Uses checkpointing for fault tolerance

### PostgreSQL Database
- Stores processed events in the `user_events` table
- Includes indexes on user_id, event_type, event_timestamp, and product_category
- Provides an `event_summary` view for basic aggregations

### Infrastructure (Docker Compose)
- PostgreSQL 15 with initialization script
- Spark Master and Worker containers
- pgAdmin for database inspection
- Shared volumes for data exchange between generator and Spark

## Data Flow

1. Generator writes CSV to `./data/input/`
2. Spark detects new file via `readStream`
3. Spark parses, transforms, and writes batch to PostgreSQL
4. Data becomes queryable in `user_events` table

## Configuration Files

- `spark_config/config.py`: Paths, PostgreSQL credentials, Spark tuning parameters
- `generator_config/config.py`: Output directory, events per file, delay between files
