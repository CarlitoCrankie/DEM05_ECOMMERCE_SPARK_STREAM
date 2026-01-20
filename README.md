```markdown
# Real-Time E-Commerce Event Pipeline

A real-time streaming pipeline that generates simulated e-commerce events, processes them using Apache Spark Structured Streaming, and stores the results in PostgreSQL — all orchestrated with Docker Compose.

docs/system_architecture.png

---

##  Overview

This project demonstrates scalable real-time data ingestion and processing using:

- **Python** — Generates simulated e-commerce events (views, purchases)
- **Apache Spark Structured Streaming** — Reads CSV events as they arrive
- **PostgreSQL** — Stores processed, cleaned events
- **Docker Compose** — Manages Spark, PostgreSQL, pgAdmin, and data generator services

---

##  Architecture

```
docs/system_architecture.png](docs/system_architecture.png)
````

---

##  Quick Start

### **1. Clone the Repository**

```bash
git clone <repository-url>
cd spark-streaming-project
````

### **2. Download PostgreSQL JDBC Driver**

```bash
mkdir -p spark/jars
curl -L -o spark/jars/postgresql-42.7.1.jar \
  https://jdbc.postgresql.org/download/postgresql-42.7.1.jar
```

### **3. Start All Services**

```bash
docker-compose up -d
```

### **4. Run the Spark Streaming Job**

```bash
docker exec -it ecommerce_spark_master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark/jars/custom/postgresql-42.7.1.jar \
  /opt/spark-apps/spark_streaming_to_postgres.py
```

### **5. Start the Data Generator**

```bash
docker exec -it ecommerce_spark_master bash -c "cd /opt/spark-apps && python3 -m generator"
```

### **6. Verify Data Flow**

```bash
docker exec -it ecommerce_postgres psql -U sparkuser -d ecommerce_events \
  -c "SELECT event_type, COUNT(*) FROM user_events WHERE user_id LIKE 'user_%' GROUP BY event_type;"
```

***

##  Project Structure

```text
spark-streaming-project/
├── .gitignore
├── docker-compose.yml
├── README.md
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
    │   ├── __main__.py
    │   ├── config.py
    │   ├── data_generator.py
    │   └── logging_config.py
    ├── jars/
    │   └── postgresql-42.7.1.jar
    └── spark_config/
        ├── __init__.py
        ├── config.py
        └── logging_config.py
```

***

##  Configuration Files

### **Data Generator (`spark/generator/config.py`)**

| Parameter             | Default               | Description                         |
| --------------------- | --------------------- | ----------------------------------- |
| OUTPUT\_DIR           | /opt/spark-data/input | Directory where CSV files are saved |
| EVENTS\_PER\_FILE     | 10                    | Rows per generated file             |
| DELAY\_BETWEEN\_FILES | 5 sec                 | Frequency of file creation          |
| TOTAL\_FILES          | 20                    | Number of files (0 = endless)       |

***

### **Spark Configuration (`spark/spark_config/config.py`)**

| Parameter                 | Default | Description                     |
| ------------------------- | ------- | ------------------------------- |
| MAX\_FILES\_PER\_TRIGGER  | 1       | Files processed per micro-batch |
| PROCESSING\_TIME\_TRIGGER | 10 sec  | Micro-batch interval            |
| SHUFFLE\_PARTITIONS       | 8       | Spark parallelism               |

***

##  Database Schema

The Spark job writes events into the `user_events` table.

| Column            | Type          | Description                  |
| ----------------- | ------------- | ---------------------------- |
| event\_id         | SERIAL        | Primary key                  |
| user\_id          | VARCHAR(50)   | User identifier              |
| event\_type       | VARCHAR(20)   | "view" or "purchase"         |
| product\_id       | VARCHAR(50)   | Product identifier           |
| product\_name     | VARCHAR(200)  | Name of product              |
| product\_category | VARCHAR(100)  | Category (Electronics, etc.) |
| price             | DECIMAL(10,2) | Item price                   |
| event\_timestamp  | TIMESTAMP     | When event occurred          |
| session\_id       | VARCHAR(100)  | Browser session              |
| device\_type      | VARCHAR(50)   | mobile, desktop, tablet      |
| inserted\_at      | TIMESTAMP     | Insertion timestamp          |

***

##  Web Interfaces

| Service              | URL                     | Credentials                  |
| -------------------- | ----------------------- | ---------------------------- |
| Spark Master UI      | <http://localhost:8080> | None                         |
| Spark Worker UI      | <http://localhost:8081> | None                         |
| Spark Application UI | <http://localhost:4040> | Visible when job running     |
| pgAdmin              | <http://localhost:5050> | <admin@admin.com> / admin123 |

***

##  Sample SQL Queries

```sql
-- Count events by type
SELECT event_type, COUNT(*)
FROM user_events
WHERE user_id LIKE 'user_%'
GROUP BY event_type;

-- Revenue per category
SELECT product_category, SUM(price) AS revenue
FROM user_events
WHERE event_type = 'purchase'
GROUP BY product_category
ORDER BY revenue DESC;

-- Events per hour
SELECT DATE_TRUNC('hour', event_timestamp) AS hour, COUNT(*)
FROM user_events
GROUP BY hour
ORDER BY hour;

-- Average processing latency
SELECT AVG(EXTRACT(EPOCH FROM (inserted_at - event_timestamp))) AS avg_latency_seconds
FROM user_events;
```

***

##  Performance Summary

| Metric         | Value                     |
| -------------- | ------------------------- |
| Avg batch time | 453 ms                    |
| Min batch time | 239 ms                    |
| Max batch time | 3862 ms (startup warm-up) |
| Avg throughput | 32.6 records/sec          |

See `docs/performance_metrics.md` for detailed results.

***

##  Troubleshooting

### Reset Spark Checkpoints

```bash
rm -rf data/checkpoints
mkdir data/checkpoints
```

### Check PostgreSQL Connectivity

```bash
docker exec -it ecommerce_postgres pg_isready -U sparkuser -d ecommerce_events
```

### View Spark Logs

```bash
docker logs ecommerce_spark_master
```

### Verify File Generation

```bash
ls -la data/input/
```

***

##  Documentation

| File                    | Description                            |
| ----------------------- | -------------------------------------- |
| **User Guide**          | `docs/user_guide.md`                   |
| **Project Overview**    | `docs/project_overview.md`             |
| **Test Cases**          | `docs/test_cases.md`                   |
| **Performance Metrics** | `docs/performance_metrics.md`          |
| **PostgreSQL Details**  | `docs/postgres_connection_details.txt` |

***

##  Requirements

*   Docker 20.10+
*   Docker Compose 2.0+
*   4GB+ RAM
*   Open ports: 5432, 5050, 7077, 8080, 8081, 4040

***

##  Technologies

*   Apache Spark 3.5.0
*   PostgreSQL 15
*   Python 3
*   Docker & Docker Compose
*   pgAdmin 4

***

##  License

MIT License


