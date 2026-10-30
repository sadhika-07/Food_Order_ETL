# Food Orders Batch ELT Pipeline

A batch-based Python, Pandas, and MySQL pipeline. It extracts the source CSV in batches of 100, preserves original values and duplicate rows in a raw MySQL database, retrieves the current run from MySQL, transforms and validates records with Pandas, then appends valid records to a separate analytics database.

## Project structure

- config.py — file, batch, and MySQL configuration
- extract.py — unchanged CSV batch extraction
- load_raw.py — transactional raw batch inserts and batch log
- retrieve_raw.py — ordered raw reads in batches
- transform.py — cross-batch deduplication, type conversion, derived fields, and rejected records
- validate.py — schema, type, duration, key, and revenue validation
- load_transformed.py — transactional analytics batch inserts
- validate_report.py — run-specific validation and execution reports
- elt_batch_pipeline.py — runs the complete workflow
- sql/setup_databases.sql — database creation statements
- sql/business_analysis.sql — requested business analysis queries
- reports/ — generated reports and rejected-record files

## Requirements

- Python 3.10 or newer
- MySQL Server running locally or reachable at the configured host
- MySQL user with permission to create databases, tables, and insert/select records
- CSV at D:ETLood_orders.csv by default, or set FOOD_ORDERS_CSV

## Setup on Windows

Open PowerShell in this project folder and run:

1. Create and activate a virtual environment (recommended):

   python -m venv .venv
   .venv\Scripts\Activate.ps1

2. Install dependencies:

   python -m pip install -r requirements.txt

3. Copy .env.example to .env (PowerShell: Copy-Item .env.example .env). Set MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, and optionally FOOD_ORDERS_CSV in .env. Do not share or commit .env; keep your password out of Python files.

4. Ensure MySQL is running. The configured user needs permission to create both databases. Alternatively, create them manually by running sql/setup_databases.sql in MySQL Workbench.

## Run the complete pipeline

From the project folder:

   python elt_batch_pipeline.py

A run gets a unique ID. Raw rows include that run ID and source row/batch numbers, while the source columns are stored as text so source values and blank fields are preserved. Each raw batch and analytics batch is inserted in its own transaction. A failed batch rolls back; the pipeline stops before downstream stages if raw loading, validation, or analytics loading fails.

The pipeline retrieves only the current run and concatenates retrieved batches before exact duplicate identification. This catches duplicate copies that fall on different batch boundaries. Re-running creates a new run and appends a new tagged copy of the input; do this only when a new ingestion run is intended.

## Transformation rules

- Exact duplicate source records: retain the first copy for analytics; record each extra copy as rejected with reason exact_duplicate_copy. All copies remain in the raw table.
- Repeated Order ID after exact duplicate removal: reject all rows for that conflicting ID for investigation rather than silently choosing one.
- Invalid or missing timestamps, nonblank unparseable financial values, negative financial values, and negative delivery durations: reject with a reason.
- Missing financial values are retained as SQL NULL, never changed to zero. Aggregates use available values and should report their non-NULL count.
- Missing payment method becomes Unknown. Missing promotion text becomes Not Specified, not No Offer.
- Platform Net Revenue is Commission Fee + Delivery Fee - Payment Processing Fee - Refunds/Chargebacks. It remains NULL unless all four inputs exist. It is a simplified assignment metric, not a complete accounting definition.
- Valid records also receive delivery_time_minutes, order_date, and order_hour.

## Outputs and validation report

After a run, reports/ receives:

- validation_report_<run_id>.md — counts, missing values, validation result, batch successes/failures
- execution_report_<run_id>.json — structured run information
- rejected_records_<run_id>.csv — excluded records with rejection reasons

The raw table is never modified during retrieval or transformation. The analytics table includes source_run_id and source_row_number for traceability.

## SQL business analysis

After a successful run, copy the run_id printed by the pipeline into the SET @run_id line at the top of sql/business_analysis.sql, then execute the script in MySQL Workbench. Each query filters to that run, avoiding double-counting if you intentionally run the pipeline again. It answers total/average order value with included row count, the most common known payment method, top channel, mean delivery time, and simplified total net revenue with included row count.

## Execution note

The project files are prepared, but the full pipeline has not been run against MySQL because this workspace does not have your configured credentials/server access. Set up .env and run the command above to generate the run-specific validation report. The existing CSV is referenced by path and is not copied into this project.


The project folder is self-contained with its source CSV copy. Run elt_batch_pipeline.py from this folder; the older D:\ETL\pipeline.py was not modified.
