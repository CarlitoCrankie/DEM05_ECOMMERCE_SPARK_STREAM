# instructions.md

```markdown
# Architecture Diagram Generation Instructions

## Scenario
Create a system architecture diagram for a real-time e-commerce event streaming pipeline using Apache Spark Structured Streaming and PostgreSQL.

---

## System Overview

**Purpose**: Process simulated e-commerce events (product views and purchases) in real-time using Spark Structured Streaming and store them in PostgreSQL for analysis.

**Architecture Pattern**: Microservices with containerized components

**Key Technologies**:
- Docker & Docker Compose (orchestration)
- Python (data generation)
- Apache Spark 3.5.0 (stream processing)
- PostgreSQL 15 (data storage)
- pgAdmin (database management)

---

## Components

### 1. **Docker Infrastructure**
- **Docker Network**: `spark_network` (bridge mode)
- **Purpose**: Isolates and connects all services
- **Volumes**:
  - `./data/input` → `/opt/spark-data/input` (CSV files)
  - `./data/checkpoints` → `/opt/spark-data/checkpoints` (Spark state)
  - `./data/logs` → `/opt/spark-data/logs` (application logs)
  - `./generator` → `/app/generator` (generator code)
  - `./spark` → `/opt/spark-apps` (Spark code)

---

### 2. **Data Generator Container**
- **Container Name**: `ecommerce_generator`
- **Base Image**: `python:3.11-slim`
- **Purpose**: Generates fake e-commerce events
- **Location**: Separate isolated container (not in Spark container)
- **Output**: CSV files written to shared volume
- **Working Directory**: `/app`

**Details**:
```
• Language: Python 3.11
• Events per file: 10
• Delay between files: 5 seconds
• Total files: 20 (configurable)
• Event types: view (85%), purchase (15%)
• Atomic writes: .tmp → .csv (prevents partial reads)
• Module structure: generator/__main__.py entry point
```

**Event Schema**:
```
- event_id (UUID)
- user_id (string)
- event_type (view/purchase)
- product_id (string)
- product_name (string)
- product_category (string)
- price (decimal)
- event_timestamp (timestamp)
- session_id (string)
- device_type (mobile/desktop/tablet)
```

**Product Categories**:
```
Electronics, Clothing, Home & Kitchen, Books,
Sports & Outdoors, Toys & Games, Beauty, Automotive
```

---

### 3. **Shared Volume**
- **Host Path**: `./data/input`
- **Container Path (Spark)**: `/opt/spark-data/input`
- **Container Path (Generator)**: `/app/data/input`
- **Purpose**: File-based communication between generator and Spark
- **Contents**: CSV files (`events_YYYYMMDD_HHMMSS_N.csv`)
- **Monitoring**: Spark monitors this directory for new files every 10 seconds

---

### 4. **Spark Cluster**

#### 4a. Spark Master
- **Container Name**: `ecommerce_spark_master`
- **Base Image**: `apache/spark:3.5.0-scala2.12-java11-python3-ubuntu`
- **Ports**:
  - `8080`: Web UI (cluster status)
  - `7077`: Cluster communication
  - `4040`: Application UI (only when streaming job running)
- **Purpose**: Coordinates the Spark cluster and manages streaming query
- **Environment**:
  - `SPARK_NO_DAEMONIZE=true`
  - `PYTHONPATH=/opt/spark-apps`

**Functions**:
```
• Cluster coordination
• Task scheduling to workers
• Resource allocation
• Streaming query lifecycle management
• Checkpoint coordination
```

#### 4b. Spark Worker
- **Container Name**: `ecommerce_spark_worker`
- **Base Image**: `apache/spark:3.5.0-scala2.12-java11-python3-ubuntu`
- **Port**: `8081` (Web UI)
- **Resources**:
  - CPU Cores: 2
  - Memory: 2GB
- **Purpose**: Executes data processing tasks (the actual executor)
- **Environment**:
  - `SPARK_WORKER_MEMORY=2G`
  - `SPARK_WORKER_CORES=2`
  - `PYTHONPATH=/opt/spark-apps`

**Processing Steps**:
```
1. Read CSV files via readStream
2. Parse with predefined schema (no inference)
3. Apply transformations:
   - Add inserted_at timestamp
   - Drop duplicates by event_id
   - Filter null values in required fields
4. Validate data:
   - event_type in ["view", "purchase"]
   - price >= 0 (if present)
   - device_type in ["mobile", "desktop", "tablet"]
   - timestamp within last 24 hours
5. Add data quality score (1.0, 0.9, or 0.8)
6. Drop quality score column
7. Write to PostgreSQL via JDBC (foreachBatch)
8. Update checkpoint
```

**Configuration**:
```
• Trigger interval: 10 seconds
• Max files per trigger: 1
• Shuffle partitions: 8
• Checkpoint location: /opt/spark-data/checkpoints
• Adaptive query execution: Enabled (disabled for streaming)
• JDBC batch size: 1000
• Isolation level: READ_COMMITTED
```

**Performance Metrics**:
```
• First batch: ~4700ms (JVM warm-up)
• Steady state: ~500-700ms per batch
• Throughput: 12-20 records/sec (after warm-up)
• Parallelism: 2 cores process partitions simultaneously
```

---

### 5. **PostgreSQL Database**
- **Container Name**: `ecommerce_postgres`
- **Base Image**: `postgres:15-alpine`
- **Port**: `5432`
- **Database**: `ecommerce_events`
- **User**: `sparkuser`
- **Password**: `sparkpass123`
- **Initialization**: `./postgres/init.sql` runs on first start

**Schema**:
```sql
Table: user_events
├── id (SERIAL PRIMARY KEY)
├── event_id (VARCHAR(36) UNIQUE NOT NULL) -- UUID from generator
├── user_id (VARCHAR(50) NOT NULL)
├── event_type (VARCHAR(20) NOT NULL)
├── product_id (VARCHAR(50) NOT NULL)
├── product_name (VARCHAR(200))
├── product_category (VARCHAR(100))
├── price (DECIMAL(10,2))
├── event_timestamp (TIMESTAMP NOT NULL)
├── session_id (VARCHAR(100))
├── device_type (VARCHAR(50))
└── inserted_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

Indexes:
├── idx_event_id (event_id) -- For deduplication
├── idx_user_id (user_id) -- For user queries
├── idx_event_type (event_type) -- For filtering
└── idx_event_timestamp (event_timestamp) -- For time-based queries

View: event_summary
├── Aggregates events by type and date
├── Shows unique users per event type
└── Calculates average price per event type
```

**Sample Queries**:
```sql
-- Event distribution
SELECT event_type, COUNT(*) FROM user_events GROUP BY event_type;

-- Revenue by category
SELECT product_category, SUM(price) 
FROM user_events 
WHERE event_type = 'purchase' 
GROUP BY product_category;

-- Processing latency
SELECT AVG(EXTRACT(EPOCH FROM (inserted_at - event_timestamp))) 
FROM user_events;
```

---

### 6. **pgAdmin**
- **Container Name**: `ecommerce_pgadmin`
- **Base Image**: `dpage/pgadmin4:latest`
- **Port**: `5050` (HTTP)
- **Purpose**: Web-based database management interface
- **Credentials**:
  - Email: `admin@admin.com`
  - Password: `admin123`

**Features**:
```
• Query editor
• Table browser
• Visual explain plans
• Database monitoring
• Connection management
```

---

### 7. **Checkpoint Storage**
- **Host Path**: `./data/checkpoints`
- **Container Path**: `/opt/spark-data/checkpoints`
- **Purpose**: Spark streaming state management for fault tolerance

**Contents**:
```
checkpoints/
├── metadata (query metadata and configuration)
├── offsets/ (tracks which files have been processed)
├── commits/ (completed batch IDs)
└── sources/ (source-specific state information)
```

**Benefits**:
```
• Fault tolerance: Resume from last position after failure
• Exactly-once semantics: No duplicate processing
• State recovery: Maintains streaming state across restarts
• Idempotency: Same files not reprocessed
```

**How it works**:
```
1. Spark processes batch 0 (file 1)
2. Writes data to PostgreSQL
3. Commits batch 0 to checkpoint
4. If crash occurs before commit: batch 0 reprocessed
5. If crash occurs after commit: batch 0 skipped, starts at batch 1
```

---

## Data Flow

### Step-by-Step Flow

```
1. Generator Container
   ├─ Runs: python -m generator
   ├─ Generates events (10 per file)
   ├─ Writes to /app/data/input/events_*.csv.tmp
   └─ Renames to .csv (atomic operation)
   
2. Shared Volume (./data/input)
   ├─ Stores CSV files
   └─ Accessible to both generator and Spark
   
3. Spark Master
   ├─ Monitors /opt/spark-data/input every 10 seconds
   ├─ Detects new CSV files
   ├─ Creates micro-batch
   └─ Assigns tasks to worker
   
4. Spark Worker (Executor)
   ├─ Reads CSV with schema
   ├─ Splits into 2 partitions (2 cores)
   ├─ Core 1: Processes partition 1
   ├─ Core 2: Processes partition 2
   ├─ Applies transformations in parallel
   ├─ Filters invalid records
   ├─ Combines results
   ├─ Writes to PostgreSQL via JDBC
   └─ Updates checkpoint
   
5. PostgreSQL Database
   ├─ Receives batch insert
   ├─ Checks unique constraint (event_id)
   ├─ Inserts new records
   ├─ Updates indexes
   └─ Returns success
   
6. pgAdmin
   └─ Queries database for monitoring
```

### Parallel Processing Within Spark Worker

```
File: events_001.csv (10 records)
  ↓
Spark splits into partitions based on SHUFFLE_PARTITIONS (8)
  ↓
Worker assigns to available cores (2)
  ↓
Core 1: Processes records 1-5
  ├─ Parse CSV
  ├─ Apply schema
  ├─ Transform (add inserted_at)
  ├─ Filter (remove nulls)
  └─ Validate (check ranges)
  
Core 2: Processes records 6-10
  ├─ Parse CSV
  ├─ Apply schema
  ├─ Transform (add inserted_at)
  ├─ Filter (remove nulls)
  └─ Validate (check ranges)
  ↓
Results combined
  ↓
Single JDBC write to PostgreSQL
  ↓
Checkpoint updated
```

---

## Connections

### Data Connections (Solid Arrows)

1. **Generator → Shared Volume**
   - Label: "CSV Files\n(events_*.csv)"
   - Color: Blue (#1976D2)
   - Style: Solid
   - Width: 2

2. **Shared Volume → Spark Master**
   - Label: "readStream\n(maxFilesPerTrigger=1)"
   - Color: Orange (#F57C00)
   - Style: Solid
   - Width: 2

3. **Spark Master → Spark Worker**
   - Label: "Task Assignment\n(micro-batch)"
   - Color: Orange (#F57C00)
   - Style: Solid
   - Width: 2

4. **Spark Worker → PostgreSQL**
   - Label: "JDBC Write\n(foreachBatch)\nBatch Insert"
   - Color: Green (#388E3C)
   - Style: Bold
   - Width: 3

### Control Connections (Dashed Arrows)

5. **Spark Worker ↔ Checkpoint Storage**
   - Label: "State Management\nOffset Tracking"
   - Color: Gray (#616161)
   - Style: Dashed
   - Width: 1

6. **PostgreSQL → pgAdmin**
   - Label: "SQL Queries\nMonitoring"
   - Color: Purple (#7B1FA2)
   - Style: Dashed
   - Width: 1

---

## Layout Rules

### Horizontal Layout (Left to Right)

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Docker Environment                            │
│                        (spark_network)                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  ┌──────────┐   ┌─────────┐   ┌──────────────┐   ┌──────────┐ │ │
│  │  │Generator │──▶│ Volume  │──▶│Spark Cluster │──▶│PostgreSQL│ │ │
│  │  │Container │   │/data/   │   │ Master+Worker│   │  :5432   │ │ │
│  │  └──────────┘   │ input   │   └──────┬───────┘   └──────────┘ │ │
│  │                 └─────────┘          │                         │ │
│  │                                      │                         │ │
│  │                                      ▼                         │ │
│  │                              ┌──────────────┐                  │ │
│  │                              │ Checkpoints  │                  │ │
│  │                              │./data/checks │                  │ │
│  │                              └──────────────┘                  │ │
│  │                                                                 │ │
│  │                              ┌──────────────┐                  │ │
│  │                              │   pgAdmin    │                  │ │
│  │                              │    :5050     │                  │ │
│  │                              └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Vertical Positioning

- **Left**: Generator Container
- **Center-Left**: Shared Volume
- **Center**: Spark Cluster (Master above Worker)
- **Center-Right**: PostgreSQL
- **Bottom-Center**: Checkpoints
- **Bottom-Right**: pgAdmin

### Clustering

1. **Outer Cluster**: Docker Environment
   - Border: Dashed, Dark Gray (#37474F)
   - Background: Light Gray (#ECEFF1)
   - Label: "Docker Environment (spark_network)"

2. **Spark Cluster**: Contains Master + Worker
   - Border: Solid, Orange (#F57C00)
   - Background: Light Orange (#FFE0B2)
   - Label: "Spark Cluster"
   - Arrangement: Master on top, Worker below

3. **Storage Cluster**: Contains PostgreSQL + pgAdmin
   - Border: Solid, Green (#388E3C)
   - Background: Light Green (#E8F5E9)
   - Label: "Data Storage & Management"

---

## Color Scheme

| Component | Background | Border | Text | Purpose |
|-----------|-----------|--------|------|---------|
| Docker Environment | `#ECEFF1` | `#37474F` | `#000000` | Infrastructure |
| Generator | `#E3F2FD` | `#1976D2` | `#000000` | Data generation |
| Shared Volume | `#F5F5F5` | `#616161` | `#000000` | Storage |
| Spark Cluster | `#FFE0B2` | `#F57C00` | `#000000` | Processing |
| Spark Master | `#FFE0B2` | `#F57C00` | `#000000` | Coordination |
| Spark Worker | `#FFCC80` | `#EF6C00` | `#000000` | Execution |
| PostgreSQL | `#E8F5E9` | `#388E3C` | `#000000` | Storage |
| pgAdmin | `#F3E5F5` | `#7B1FA2` | `#000000` | Management |
| Checkpoints | `#FFF9C4` | `#F9A825` | `#000000` | State |

---

## Annotations

### Generator Container
```
Data Generator
(Python Container)

• Creates CSV files
• 10 events/file
• 5s intervals
• Atomic writes (.tmp → .csv)
• Isolated container
```

### Shared Volume
```
Shared Volume
./data/input

• CSV file storage
• Monitored by Spark
• Shared between containers
```

### Spark Master
```
Spark Master
:8080 (Web UI)
:7077 (Cluster)

• Coordinates cluster
• Manages streaming query
• Assigns tasks to workers
• Monitors checkpoints
```

### Spark Worker
```
Spark Worker
:8081 (Web UI)

• 2 cores, 2GB RAM
• Parse CSV files
• Transform data
• Filter nulls
• Validate ranges
• JDBC write
• ~500ms per batch
```

### PostgreSQL
```
PostgreSQL 15
:5432

Database: ecommerce_events
Table: user_events
Indexes: event_id, user_id, 
         event_type, event_timestamp
View: event_summary
```

### pgAdmin
```
pgAdmin
:5050

• Web UI
• Database management
• Query editor
• Monitoring
```

### Checkpoints
```
Checkpoint Storage
./data/checkpoints

• Fault tolerance
• Offset tracking
• Exactly-once semantics
• State recovery
```

---

## Performance Metrics to Include

Add a legend box showing:

```
Performance Metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Throughput:     10 records/file
Batch Time:     ~500ms (avg)
                ~4700ms (first batch)
Latency:        10-15 seconds
Trigger:        Every 10 seconds
Parallelism:    2 cores
Files/Trigger:  1
Warm-up:        ~20-30 batches
Peak Throughput: 20 rec/sec
```

---

## Output Format Requirements

### File Naming
- Base name: `ecommerce_streaming_architecture`
- PNG: `ecommerce_streaming_architecture.png`
- DOT: `ecommerce_streaming_architecture.dot`
- DRAWIO: `ecommerce_streaming_architecture.drawio`

### Image Specifications
- **Format**: PNG
- **Resolution**: 300 DPI minimum
- **Size**: Optimized for A4 landscape (11.7" × 8.3")
- **Background**: White
- **Margins**: 0.5 inches all sides
- **Border**: None

### Text Requirements
- **Font Family**: Sans-serif (Helvetica, Arial)
- **Title**: 16pt bold
- **Component labels**: 12pt regular
- **Annotations**: 10pt regular
- **Port numbers**: 9pt italic
- **All text must be readable at 100% zoom**
- **No text overlap**

### Graph Attributes
```python
graph_attr = {
    "fontsize": "12",
    "fontname": "Helvetica",
    "bgcolor": "white",
    "pad": "0.5",
    "nodesep": "1.0",
    "ranksep": "1.5",
    "splines": "ortho",
    "rankdir": "LR",
    "concentrate": "false"
}
```

---

## Validation Checklist

Before finalizing, verify:

### Components
- [ ] Generator container visible and labeled
- [ ] Shared volume shown with path
- [ ] Spark Master shown with ports
- [ ] Spark Worker shown with resources
- [ ] PostgreSQL shown with port
- [ ] pgAdmin shown with port
- [ ] Checkpoint storage shown

### Connections
- [ ] Generator → Volume arrow
- [ ] Volume → Spark Master arrow
- [ ] Spark Master → Spark Worker arrow
- [ ] Spark Worker → PostgreSQL arrow
- [ ] Spark Worker ↔ Checkpoints arrow
- [ ] PostgreSQL → pgAdmin arrow

### Labels
- [ ] All arrows labeled
- [ ] All ports displayed
- [ ] Resource allocations shown
- [ ] Processing steps listed

### Visual
- [ ] Docker network boundary visible
- [ ] Spark cluster grouped
- [ ] Color coding consistent
- [ ] No overlapping text
- [ ] All text readable

### Files
- [ ] PNG generated
- [ ] DOT generated
- [ ] DRAWIO generated
- [ ] All saved to docs/diagrams/

---

## Additional Notes

### Scalability Indicators
Show where horizontal scaling is possible:
- **Spark Workers**: Can add more worker containers
  - Annotation: "Horizontally scalable"
- **Generator**: Can run multiple generator instances
  - Annotation: "Can run multiple instances"

### Fault Tolerance Highlights
Use special visual treatment for checkpoint mechanism:
- Dashed bidirectional arrow
- Different color (gray)
- Annotation explaining recovery process

### Security Notes
Add small disclaimer:
```
Note: Development configuration
Production requires:
• Encrypted connections (SSL/TLS)
• Secret management (Vault)
• Network policies
• Authentication & authorization
```

### Technology Versions
Include version information:
```
Technology Stack
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Docker Compose:  2.0+
Python:          3.11
Spark:           3.5.0
PostgreSQL:      15-alpine
pgAdmin:         Latest
Java:            11
Scala:           2.12
```

---

## Example Use Cases to Illustrate

### Use Case 1: Normal Operation
```
1. Generator creates events_001.csv (10 records)
2. Spark detects file after 10 seconds
3. Worker processes in 500ms
4. Data appears in PostgreSQL
5. pgAdmin shows new records
```

### Use Case 2: Fault Recovery
```
1. Spark processes batch 5
2. Writes to PostgreSQL
3. Crashes before checkpoint commit
4. Restart Spark
5. Reads checkpoint: batch 5 not committed
6. Reprocesses batch 5
7. PostgreSQL unique constraint prevents duplicates
```

### Use Case 3: Duplicate Handling
```
1. Generator creates file with duplicate event_id
2. Spark processes file
3. dropDuplicates() removes duplicate in memory
4. PostgreSQL unique constraint as backup
5. Only one record inserted
```

---
```

This instructions.md file provides comprehensive specifications for generating your architecture diagram, including all components, connections, colors, annotations, and validation criteria. It's detailed enough for an LLM to generate an accurate diagram automatically.