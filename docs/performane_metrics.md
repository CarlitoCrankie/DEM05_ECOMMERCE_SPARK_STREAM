# Performance Metrics Report

## Test Environment

- **Host OS:** Windows (WSL2 with kernel 6.6.87.2-microsoft-standard-WSL2)
- **CPU:** Not specified (available via Docker)
- **RAM:** 15.49 GiB (Docker limit)
- **Docker Resources:** 15.49 GiB RAM allocated
- **Spark Worker Config:** 2 cores, 2GB memory

## Test Parameters

- Events per CSV file: 10
- Files generated: 20
- Total events: 200
- Trigger interval: 10 seconds
- Max files per trigger: 1

## Measurements

### Throughput

| Metric | Value |
|--------|-------|
| Total events processed | 200 |
| Total processing time | 190 seconds (11:11:01 to 11:14:10) |
| Average events/second | 1.05 |
| Files processed | 20 |

### Latency (per batch)

| Metric | Value |
|--------|-------|
| Minimum batch time | 239 ms (Batch 16) |
| Maximum batch time | 3,862 ms (Batch 0) |
| Average batch time | 453 ms |
| Median batch time | 299 ms |

### Batch Processing Details

| Batch | Records | Processing Time (ms) | Throughput (records/sec) |
|-------|---------|---------------------|--------------------------|
| 0 | 10 | 3,862 | 2.59 |
| 1 | 10 | 485 | 20.62 |
| 2 | 10 | 371 | 26.95 |
| 3 | 10 | 403 | 24.81 |
| 4 | 10 | 404 | 24.75 |
| 5 | 10 | 307 | 32.57 |
| 6 | 10 | 284 | 35.21 |
| 7 | 10 | 374 | 26.74 |
| 8 | 10 | 392 | 25.51 |
| 9 | 10 | 281 | 35.59 |
| 10 | 10 | 301 | 33.22 |
| 11 | 10 | 255 | 39.22 |
| 12 | 10 | 295 | 33.90 |
| 13 | 10 | 276 | 36.23 |
| 14 | 10 | 253 | 39.53 |
| 15 | 10 | 314 | 31.85 |
| 16 | 10 | 239 | 41.84 |
| 17 | 10 | 288 | 34.72 |
| 18 | 10 | 253 | 39.53 |
| 19 | 10 | 251 | 39.84 |

### End-to-End Latency

Time from CSV file creation to record visible in PostgreSQL:

| Metric | Value |
|--------|-------|
| Minimum | 166.34 seconds |
| Maximum | 455.23 seconds |
| Average | 282.42 seconds |

### Resource Usage (during processing)

| Resource | Spark Master | Spark Worker | PostgreSQL |
|----------|--------------|--------------|------------|
| CPU % | 0.13% | 0.18% | 0.00% |
| Memory MB | 373.2 MiB | 286 MiB | 34.76 MiB |

## Observations

- Batch 0 had significantly higher processing time (3,862 ms) due to JVM warm-up and initial JDBC connection establishment
- After warm-up, batch processing times stabilized between 239-485 ms
- Average throughput per batch (excluding Batch 0): 32.6 records/sec
- CPU utilization remained low, indicating I/O-bound workload
- Event distribution matched expected weights: ~85% view events, ~15% purchase events

## How to Collect These Metrics

1. **Batch processing time:** Logged by `write_to_postgres()` function
2. **Throughput:** `SELECT COUNT(*) FROM user_events;` divided by total runtime
3. **Resource usage:** `docker stats` during processing
4. **End-to-end latency:** Compare `event_timestamp` with `inserted_at` in PostgreSQL:
   ```sql
   SELECT AVG(EXTRACT(EPOCH FROM (inserted_at - event_timestamp))) as avg_latency_seconds
   FROM user_events
   WHERE user_id LIKE 'user_%';
