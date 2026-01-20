# User Guide

Step-by-step instructions for setting up and running the **E-Commerce Streaming Pipeline**.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Directory Structure](#directory-structure)
- [Setup Instructions](#setup-instructions)
  - [Step 1: Download PostgreSQL JDBC Driver](#step-1-download-postgresql-jdbc-driver)
  - [Step 2: Start Infrastructure](#step-2-start-infrastructure)
  - [Step 3: Verify PostgreSQL Setup](#step-3-verify-postgresql-setup)
  - [Step 4: Start Spark Streaming Job](#step-4-start-spark-streaming-job)
  - [Step 5: Run Data Generator](#step-5-run-data-generator)
  - [Step 6: Verify Data Flow](#step-6-verify-data-flow)
- [Stopping the Pipeline](#stopping-the-pipeline)
- [Web Interfaces](#web-interfaces)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Minimum Version |
|-------------|-----------------|
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| Python | 3.8+ |
| Available RAM | 4GB |

**Required Ports**

- `5432` - PostgreSQL
- `5050` - pgAdmin
- `7077` - Spark Master
- `8080` - Spark Master UI
- `8081` - Spark Worker UI
- `4040` - Spark Application UI

---

## Directory Structure

spark-streaming-project/
├── .gitignore
├── docker-compose.yml
├── data/
│   ├── checkpoints/
│   ├── input/
│   └── logs/
│       ├── spark_errors.log
│       └── spark_streaming.log
├── docs/
│   ├── performance_metrics.md
│   ├── postgres_connection_details.txt
│   ├── project_overview.md
│   ├── system_architecture.png
│   ├── test_cases.md
│   └── user_guide.md
├── postgres/
│   └── init.sql
└── spark/
    ├── __init__.py
    ├── spark_streaming_to_postgres.py
    ├── generator/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── config.py
    │   ├── data_generator.py
    │   └── logging_config.py
    ├── jars/
    │   └── postgresql-42.7.1.jar
    └── spark_config/
        ├── __init__.py
        ├── config.py
        └── logging_config.py

***

## **Setup Instructions**

***

### Step 1: Download PostgreSQL JDBC Driver

Spark needs the PostgreSQL JDBC driver to write to the database.

```bash
mkdir -p spark/jars
curl -L -o spark/jars/postgresql-42.7.1.jar \
  https://jdbc.postgresql.org/download/postgresql-42.7.1.jar
```

Verify the download:

```bash
ls -la spark/jars/
```

Expected:

    -rw-r--r-- 1 user user 1083629 postgresql-42.7.1.jar

***

### **Step 2: Start Infrastructure**

Start all services:

```bash
docker-compose up -d
```

Check status:

```bash
docker-compose ps
```

Expected:

    NAME                    STATUS
    ecommerce_postgres      Up (healthy)
    ecommerce_spark_master  Up
    ecommerce_spark_worker  Up
    ecommerce_pgadmin       Up

Wait until PostgreSQL shows **healthy**.

***

### **Step 3: Verify PostgreSQL Setup**

#### **Option A — Using CLI**

```bash
docker exec -it ecommerce_postgres psql -U sparkuser -d ecommerce_events \
  -c "SELECT COUNT(*) FROM user_events;"
```

Example output:

     count
    -------
         2

#### **Option B — Using pgAdmin**

1.  Visit: **<http://localhost:5050>**
2.  Login → `admin@admin.com` / `admin123`
3.  Add server:
    *   Host: `postgres`
    *   Port: `5432`
    *   DB: `ecommerce_events`
    *   User: `sparkuser`
    *   Password: `sparkpass123`

***

### **Step 4: Start Spark Streaming Job**

```bash
docker exec -it ecommerce_spark_master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark/jars/custom/postgresql-42.7.1.jar \
  /opt/spark-apps/spark_streaming_to_postgres.py
```

Expected logs:

    INFO: Creating Spark session...
    INFO: Starting streaming query...
    INFO: Monitoring for new CSV files...

Keep this terminal open.

***

### **Step 5: Run Data Generator**

Open another terminal:

```bash
docker exec -it ecommerce_spark_master bash -c "cd /opt/spark-apps && python3 -m generator"
```

Expected output:

    INFO: Data generator started
    INFO: File committed: events_20240115_143022_1.csv | events=100

Spark terminal should display:

    INFO: Processing batch 0 with 10 records
    INFO: Batch 0 written successfully to PostgreSQL

***

### **Step 6: Verify Data Flow**

Run:

```bash
docker exec -it ecommerce_postgres psql -U sparkuser -d ecommerce_events \
  -c "SELECT event_type, COUNT(*) FROM user_events WHERE user_id LIKE 'user_%' GROUP BY event_type;"
```

Example:

    event_type | count
    ------------+-------
    view       |    85
    purchase   |    15


Check Spark UI at: **<http://localhost:4040>**

***

## **Stopping the Pipeline**

1.  Stop data generator (Ctrl+C)
2.  Stop Spark job (Ctrl+C)
3.  Stop Docker stack:

```bash
docker-compose down
```

To wipe all data:

```bash
docker-compose down -v
```

***

## **Web Interfaces**

| Interface            | URL                     | Description                    |
| -------------------- | ----------------------- | ------------------------------ |
| Spark Master UI      | <http://localhost:8080> | Cluster overview               |
| Spark Application UI | <http://localhost:4040> | Batch metrics (while job runs) |
| Spark Worker UI      | <http://localhost:8081> | Worker information             |
| pgAdmin              | <http://localhost:5050> | Database UI                    |

***

## **Troubleshooting**

***

### **PostgreSQL Connection Refused**

```bash
docker exec -it ecommerce_postgres pg_isready -U sparkuser -d ecommerce_events
docker logs ecommerce_postgres
```

***

### **No Data Appearing in PostgreSQL**

Check for CSV files:

```bash
ls -la data/input/
```

Check for temp files:

```bash
ls data/input/*.tmp
```

Check Spark logs:

```bash
docker logs ecommerce_spark_master
```

***

### **Spark UI Missing (4040)**

Start the streaming job first — UI appears only while active.

***

### **Out of Memory Errors**

Fixes:

*   Increase Docker RAM
*   Reduce events per file in `generator/config.py`
*   Reduce Spark worker memory in `docker-compose.yml`

***

### **Duplicate Data After Restart**

Clear checkpoints:

```bash
rm -rf data/checkpoints
mkdir data/checkpoints
rm -rf data/input/*
```

Restart services.

***

### **JDBC Driver Not Found**

Verify:

```bash
ls spark/jars/postgresql-42.7.1.jar
```

Re-download if missing:

```bash
curl -L -o spark/jars/postgresql-42.7.1.jar \
  https://jdbc.postgresql.org/download/postgresql-42.7.1.jar
```

