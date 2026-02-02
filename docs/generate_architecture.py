#!/usr/bin/env python3
"""
E-Commerce Streaming Pipeline Architecture Diagram Generator

This script generates a system architecture diagram for a real-time e-commerce 
event streaming pipeline using Apache Spark Structured Streaming and PostgreSQL.

Output files:
- ecommerce_streaming_architecture.png (PNG image)
- ecommerce_streaming_architecture.dot (GraphViz source)
- ecommerce_streaming_architecture.drawio (Editable Draw.io format)
"""

import os
import subprocess
from pathlib import Path
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.container import Docker
from diagrams.onprem.compute import Server
from diagrams.programming.language import Python
from diagrams.onprem.analytics import Spark
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Internet
from diagrams.generic.storage import Storage
from diagrams.generic.device import Mobile


def generate_architecture_diagram():
    """Generate the architecture diagram with all components and connections."""
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent / "diagrams"
    output_dir.mkdir(exist_ok=True)
    
    # Graph attributes for layout control
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
    
    # Define cluster attributes with colors (for newer diagrams version)
    docker_cluster_attr = {
        "style": "dashed",
    }
    
    generator_cluster_attr = {}
    
    spark_cluster_attr = {}
    
    storage_cluster_attr = {}
    
    checkpoint_cluster_attr = {}
    
    # Edge styles
    edge_csv = Edge(label="CSV Files\n(events_*.csv)", color="blue", style="solid", penwidth="2")
    edge_readstream = Edge(label="readStream\n(maxFilesPerTrigger=1)", color="orange", style="solid", penwidth="2")
    edge_task = Edge(label="Task Assignment\n(micro-batch)", color="orange", style="solid", penwidth="2")
    edge_jdbc = Edge(label="JDBC Write\n(foreachBatch)\nBatch Insert", color="green", style="bold", penwidth="3")
    edge_checkpoint = Edge(label="State Management\nOffset Tracking", color="gray", style="dashed", penwidth="1")
    edge_query = Edge(label="SQL Queries\nMonitoring", color="purple", style="dashed", penwidth="1")
    
    with Diagram(
        "E-Commerce Streaming Architecture",
        filename=str(output_dir / "ecommerce_streaming_architecture"),
        direction="LR",
        graph_attr=graph_attr,
        outformat=["png", "dot"],
        show=False
    ):
        
        with Cluster("Docker Infrastructure"):
            
            # Data Generation Layer
            with Cluster("Data Generation"):
                generator = Python("Data Generator\n(Python Container)\n\n• 10 events/file\n• 5s intervals\n• Atomic writes")
            
            # Shared Volume
            shared_volume = Storage("Shared Volume\n./data/input\n\n• CSV file storage\n• Monitored by Spark")
            
            # Stream Processing Layer
            with Cluster("Stream Processing (Spark Cluster)"):
                spark_master = Spark("Spark Master\n:8080 :7077\n\n• Coordinates cluster\n• Manages query\n• Assigns tasks")
                spark_worker = Spark("Spark Worker\n:8081\n\n• 2 cores, 2GB RAM\n• Parse CSV\n• Transform data\n• ~500ms/batch")
            
            # Checkpoint Storage Layer
            with Cluster("State Management"):
                checkpoints = Storage("Checkpoint Storage\n./data/checkpoints\n\n• Fault tolerance\n• Offset tracking\n• Exactly-once")
            
            # Data Storage Layer
            with Cluster("Data Storage & Management"):
                postgres = PostgreSQL("PostgreSQL 15\n:5432\n\nDatabase: ecommerce_events\nTable: user_events\nIndexes: event_id, user_id,\nevent_type, timestamp")
                pgadmin = Server("pgAdmin\n:5050\n\n• Web UI\n• DB Management\n• Query Editor")
            
            # Data Flow Connections
            generator >> edge_csv >> shared_volume
            shared_volume >> edge_readstream >> spark_master
            spark_master >> edge_task >> spark_worker
            spark_worker >> edge_jdbc >> postgres
            spark_worker >> edge_checkpoint >> checkpoints
            postgres >> edge_query >> pgadmin
    
    print(f"✓ Architecture diagram generated successfully!")
    print(f"  Location: {output_dir}")
    print(f"  Files created:")
    print(f"    - ecommerce_streaming_architecture.png")
    print(f"    - ecommerce_streaming_architecture.dot")
    
    # Convert DOT to Draw.io format (optional)
    dot_file = output_dir / "ecommerce_streaming_architecture.dot"
    drawio_file = output_dir / "ecommerce_streaming_architecture.drawio"
    
    try:
        print(f"\n  Converting to Draw.io format...")
        subprocess.run(
            ["graphviz2drawio", str(dot_file), "-o", str(drawio_file)],
            check=True,
            capture_output=True
        )
        print(f"    - ecommerce_streaming_architecture.drawio")
        print(f"✓ All diagram formats generated successfully!")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\n⚠ Draw.io conversion skipped (graphviz2drawio not available)")
        print(f"  Note: The PNG and DOT files were created successfully.")
        print(f"  To generate Draw.io format, install C++ build tools and graphviz2drawio.")


if __name__ == "__main__":
    try:
        generate_architecture_diagram()
    except Exception as e:
        print(f"✗ Error generating architecture diagram: {e}")
        print(f"\nMake sure GraphViz is installed on your system:")
        print(f"  - Windows: https://graphviz.org/download/")
        print(f"  - Linux: sudo apt-get install graphviz")
        print(f"  - Mac: brew install graphviz")
        raise
