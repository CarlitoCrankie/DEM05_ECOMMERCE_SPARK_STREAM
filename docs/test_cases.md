
---

## 4. test_cases.md

```markdown
# Test Cases: E-Commerce Streaming Pipeline

## TC-01: CSV File Generation

**Objective:** Verify generator creates valid CSV files

**Steps:**
1. Run `python -m generator.data_generator`
2. Wait for one file to be created
3. Inspect file in `./data/input/`

**Expected:**
- File named `events_YYYYMMDD_HHMMSS_N.csv`
- Contains header row with 9 columns
- Contains configured number of data rows (default: 100)
- No `.tmp` files remain

**Actual:** [Fill after testing]

**Status:** [ ] Pass / [ ] Fail

---

## TC-02: Spark Detects New Files

**Objective:** Verify Spark picks up new CSV files

**Steps:**
1. Start Spark streaming job
2. Copy a CSV file into `./data/input/`
3. Check Spark logs

**Expected:**
- Log shows "Processing batch X with Y records"
- Batch ID increments

**Actual:** [Fill after testing]

**Status:** [ ] Pass / [ ] Fail

---

## TC-03: Data Transformation

**Objective:** Verify transformations are applied

**Steps:**
1. Process a batch through Spark
2. Query PostgreSQL: `SELECT inserted_at FROM user_events ORDER BY event_id DESC LIMIT 5;`

**Expected:**
- `inserted_at` column is populated
- Timestamp is close to current time

**Actual:** [Fill after testing]

**Status:** [ ] Pass / [ ] Fail

---

## TC-04: Null Filtering

**Objective:** Verify records with null required fields are dropped

**Steps:**
1. Manually create a CSV with a row where `user_id` is empty
2. Process through Spark
3. Query PostgreSQL for that record

**Expected:**
- Record with null user_id is not in database

**Actual:** [Fill after testing]

**Status:** [ ] Pass / [ ] Fail

---

## TC-05: PostgreSQL Write Success

**Objective:** Verify data reaches PostgreSQL

**Steps:**
1. Note current count: `SELECT COUNT(*) FROM user_events;`
2. Generate one CSV file (e.g., 100 events)
3. Wait for Spark to process
4. Check count again

**Expected:**
- Count increases by ~100 (minus any filtered nulls)

**Actual:** [Fill after testing]

**Status:** [ ] Pass / [ ] Fail

---

## TC-06: Checkpoint Recovery

**Objective:** Verify Spark resumes correctly after restart

**Steps:**
1. Process several files
2. Stop Spark job (Ctrl+C)
3. Add new CSV files
4. Restart Spark job
5. Check if new files are processed and old files are not reprocessed

**Expected:**
- Only new files processed
- No duplicate records in PostgreSQL

**Actual:** [Fill after testing]

**Status:** [ ] Pass / [ ] Fail

---

## TC-07: Event Type Distribution

**Objective:** Verify event type ratio matches generator weights

**Steps:**
1. Generate 1000+ events
2. Query: `SELECT event_type, COUNT(*) FROM user_events GROUP BY event_type;`

**Expected:**
- ~85% view events
- ~15% purchase events

**Actual:** [Fill after testing]

**Status:** [ ] Pass / [ ] Fail
