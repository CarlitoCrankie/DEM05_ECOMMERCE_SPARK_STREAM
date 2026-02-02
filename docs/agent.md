# agent.md

```markdown
# Agent Instructions: E-Commerce Streaming Pipeline Architecture Diagram Generation

## Overview
This workspace contains tools to automatically generate architecture diagrams for a real-time data streaming pipeline. The system uses Apache Spark Structured Streaming to process e-commerce events from CSV files and store them in PostgreSQL. Diagrams are created using Python's `diagrams` library, rendered with GraphViz, and converted to editable draw.io format.

---

## Environment Setup

### Python Environment
- **Python Version**: 3.8+
- **Virtual Environment**: Recommended for isolation
- **Activation**: 
  - Windows: `.\venv\Scripts\activate`
  - Linux/Mac: `source venv/bin/activate`

### Installed Packages (Required Versions)
```
diagrams==0.24.4
graphviz==0.20.3
graphviz2drawio==1.1.0
```

### Initial Setup from Scratch
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install packages
pip install -r requirements.txt
```

### GraphViz Installation
- **Windows**: Download from https://graphviz.org/download/ and install to `C:\Program Files\Graphviz`
- **Linux**: `sudo apt-get install graphviz`
- **Mac**: `brew install graphviz`

**Critical**: Add GraphViz to PATH:
```bash
# Windows (PowerShell)
$env:PATH += ";C:\Program Files\Graphviz\bin"

# Linux/Mac
export PATH=$PATH:/usr/local/bin
```

### VS Code Extensions (Recommended)
- **Draw.io Integration**: `hediet.vscode-drawio` - For viewing/editing .drawio files
- **Docker**: `ms-azuretools.vscode-docker` - For container management

---

## Project Structure

```
spark-streaming-project/
├── docs/
│   ├── diagrams/                      # Output directory for generated diagrams
│   │   ├── *.png                      # PNG image outputs
│   │   ├── *.dot                      # GraphViz DOT source files
│   │   └── *.drawio                   # Editable draw.io files
│   ├── agent.md                       # THIS FILE - Agent instructions
│   ├── requirements.txt               # Python dependencies for diagram generation
│   ├── instructions.md                # Detailed architecture specification
│   ├── generate_architecture.py       # Main diagram generation script
│   ├── performance_metrics.md
│   ├── project_overview.md
│   ├── test_cases.md
│   └── user_guide.md
├── docker-compose.yml
├── README.md
├── data/
│   ├── input/                         # CSV files from generator
│   ├── checkpoints/                   # Spark checkpoints
│   └── logs/                          # Application logs
├── generator/                         # Data generator (separate container)
│   ├── __init__.py
│   ├── __main__.py
│   ├── data_generator.py
│   ├── config.py
│   └── logging_config.py
├── postgres/
│   └── init.sql                       # Database initialization
└── spark/
    ├── __init__.py
    ├── spark_streaming_to_postgres.py
    ├── spark_config/
    │   ├── __init__.py
    │   ├── config.py
    │   └── logging_config.py
    └── jars/
        └── postgresql-42.7.1.jar
```

---

## Diagram Generation Workflow

### Complete Process (3 Steps)

#### Step 1: Create Python Diagram Script
- Import required components from `diagrams` library
- Use proper icon names for Docker, Spark, PostgreSQL, Python
- Configure graph attributes for clean layout:
  ```python
  graph_attr = {
      "splines": "ortho",      # Orthogonal lines
      "nodesep": "1.0",        # Node spacing
      "ranksep": "1.5",        # Rank spacing
      "fontsize": "12",
      "bgcolor": "white",
      "pad": "0.5",
      "rankdir": "LR"          # Left to right flow
  }
  ```
- Use Cluster for Docker containers and logical grouping
- Set different background colors for different components
- Set output format: `outformat=["png", "dot"]`

#### Step 2: Run with GraphViz in PATH
```bash
cd docs/
python generate_architecture.py
```

#### Step 3: Convert DOT to Draw.io
This happens automatically in the script using:
```python
subprocess.run([
    "graphviz2drawio", 
    "diagrams/ecommerce_streaming_architecture.dot", 
    "-o", 
    "diagrams/ecommerce_streaming_architecture.drawio"
], check=True)
```

---

## Component Icons and Imports

### Required Imports
```python
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.container import Docker
from diagrams.onprem.compute import Server
from diagrams.programming.language import Python
from diagrams.onprem.analytics import Spark
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Internet
from diagrams.generic.storage import Storage
from diagrams.generic.database import SQL
```

### Component Mapping

| Component | Icon Class | Label |
|-----------|-----------|-------|
| Data Generator | `Python` | "Data Generator\n(Python Container)" |
| Shared Volume | `Storage` | "Shared Volume\n./data/input" |
| Spark Master | `Spark` | "Spark Master\n:8080 :7077" |
| Spark Worker | `Spark` | "Spark Worker\n:8081\n2 cores, 2GB RAM" |
| PostgreSQL | `PostgreSQL` | "PostgreSQL\n:5432" |
| pgAdmin | `Server` | "pgAdmin\n:5050" |
| Checkpoints | `Storage` | "Checkpoint Storage\n./data/checkpoints" |
| Docker Network | `Docker` | Container wrapper |

---

## Color Coding for Components

Use different background colors to distinguish component types:

```python
# Data Generation Layer
generator_cluster_attr = {
    "fontsize": "13",
    "bgcolor": "#E3F2FD",  # Light Blue
    "style": "rounded",
    "margin": "15",
    "label": "Data Generation"
}

# Processing Layer
spark_cluster_attr = {
    "fontsize": "13",
    "bgcolor": "#FFE0B2",  # Light Orange
    "style": "rounded",
    "margin": "15",
    "label": "Stream Processing"
}

# Storage Layer
storage_cluster_attr = {
    "fontsize": "13",
    "bgcolor": "#E8F5E9",  # Light Green
    "style": "rounded",
    "margin": "15",
    "label": "Data Storage"
}

# Management Layer
management_cluster_attr = {
    "fontsize": "13",
    "bgcolor": "#F3E5F5",  # Light Purple
    "style": "rounded",
    "margin": "15",
    "label": "Management & Monitoring"
}

# Infrastructure Layer
docker_cluster_attr = {
    "fontsize": "14",
    "bgcolor": "#ECEFF1",  # Light Gray
    "style": "dashed",
    "margin": "20",
    "label": "Docker Environment"
}
```

---

## Data Flow Arrows

### Arrow Styles and Labels

```python
# CSV file flow
Edge(label="CSV Files\n(events_*.csv)", color="blue", style="solid")

# Stream reading
Edge(label="readStream\n(maxFilesPerTrigger=1)", color="orange", style="solid")

# JDBC write
Edge(label="JDBC Write\n(foreachBatch)", color="green", style="bold")

# Checkpoint management
Edge(label="State Management", color="gray", style="dashed")

# SQL queries
Edge(label="SQL Queries", color="purple", style="dashed")
```

---

## Architecture Layers

### Layer 1: Docker Infrastructure
- Outer container representing Docker environment
- Contains all services
- Network: `spark_network`

### Layer 2: Data Generation
- Generator container (isolated)
- Writes to shared volume
- Python-based event simulator

### Layer 3: Stream Processing
- Spark Master (coordinator)
- Spark Worker (executor with 2 cores, 2GB RAM)
- Processes CSV files in micro-batches
- Applies transformations and validations

### Layer 4: Data Storage
- PostgreSQL database
- Stores processed events
- Indexed for query performance

### Layer 5: Management
- pgAdmin (database UI)
- Checkpoint storage (fault tolerance)

---

## Key Metrics to Display

Include these annotations in the diagram:

```python
# Generator
"• 10 events/file\n• 5s intervals\n• Atomic writes"

# Spark Worker
"• Parse CSV\n• Transform\n• Filter nulls\n• 2 cores, 2GB RAM"

# PostgreSQL
"• Table: user_events\n• Indexes: user_id, event_type\n• View: event_summary"

# Checkpoints
"• Fault tolerance\n• Exactly-once semantics\n• Offset tracking"
```

---

## Troubleshooting

### GraphViz Not Found
**Error**: `ExecutableNotFound: failed to execute 'dot'`

**Solution**: 
```bash
# Windows
$env:PATH += ";C:\Program Files\Graphviz\bin"

# Linux/Mac
export PATH=$PATH:/usr/local/bin
```

### Import Errors
**Error**: `cannot import name 'Spark'`

**Solution**: Check available icons:
```python
from diagrams.onprem import analytics
print([x for x in dir(analytics) if not x.startswith('_')])
```

### Layout Issues
**Issue**: Cluttered or overlapping components

**Solutions**:
1. Adjust `nodesep` and `ranksep` in graph_attr
2. Change `rankdir` from "LR" to "TB" (top-bottom)
3. Simplify cluster nesting
4. Manually refine in draw.io after generation

---

## Output Files

Each diagram generation produces 3 files:

1. **PNG** (`ecommerce_streaming_architecture.png`)
   - Static image for documentation
   - ~150-250 KB

2. **DOT** (`ecommerce_streaming_architecture.dot`)
   - GraphViz source (text format)
   - Version control friendly
   - ~8-12 KB

3. **DRAWIO** (`ecommerce_streaming_architecture.drawio`)
   - Editable in VS Code or draw.io
   - For manual refinement
   - ~100-200 KB

**Location**: All files saved to `docs/diagrams/`

---

## Example Architecture Components

### Container Hierarchy
```
Docker Environment
├── Generator Container
│   └── Python Data Generator
├── Spark Cluster
│   ├── Spark Master (:8080, :7077)
│   └── Spark Worker (:8081)
├── PostgreSQL Container (:5432)
└── pgAdmin Container (:5050)

Shared Resources
├── Volume: ./data/input (CSV files)
└── Volume: ./data/checkpoints (state)
```

### Data Flow
```
Generator → CSV Files → Spark (readStream) → Transform → PostgreSQL
                                    ↓
                              Checkpoints (fault tolerance)
                                    ↓
                              pgAdmin (monitoring)
```

---

## Key Principles

1. **Isolation First**: Each service in its own container
2. **Clear Data Flow**: Left-to-right progression (Generator → Spark → PostgreSQL)
3. **Color Coding**: Different colors for different layers
4. **Annotations**: Include ports, resource limits, and key functions
5. **Fault Tolerance**: Show checkpoint mechanism clearly
6. **Scalability**: Indicate where horizontal scaling is possible

---

## Validation Checklist

Before finalizing the diagram, verify:

- [ ] All 5 containers shown (Generator, Spark Master, Spark Worker, PostgreSQL, pgAdmin)
- [ ] Shared volumes clearly indicated
- [ ] Docker network boundary visible
- [ ] Data flow arrows with labels
- [ ] Port numbers displayed
- [ ] Resource allocations shown (cores, memory)
- [ ] Checkpoint mechanism illustrated
- [ ] Color coding consistent
- [ ] All text readable at 100% zoom
- [ ] PNG, DOT, and DRAWIO files generated

---

## Performance Considerations

The diagram should illustrate:

- **Throughput**: 10 records/file, 1 file per 10-second trigger
- **Latency**: ~500ms per batch (after warm-up)
- **Parallelism**: 2 cores processing partitions simultaneously
- **Fault Tolerance**: Checkpoint-based recovery
- **Scalability**: Can add more Spark workers

---

## Next Steps After Generation

1. **Review PNG**: Check overall layout and readability
2. **Inspect DOT**: Verify all connections are correct
3. **Refine in Draw.io**: 
   - Adjust spacing
   - Add detailed annotations
   - Align components
   - Add legend if needed
4. **Export final PNG**: High resolution (300 DPI) for documentation
5. **Commit to Git**: Include all three formats

---
```

This agent.md file provides complete instructions for an LLM to understand the project context, setup requirements, and diagram generation workflow. It follows the same structure as your Azure example but adapted for your Spark Streaming project.