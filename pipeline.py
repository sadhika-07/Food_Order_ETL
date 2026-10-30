from uuid import uuid4
import pandas as pd
from config import ANALYTICS_DATABASE, BATCH_SIZE, CSV_PATH, PROJECT_DIR, RAW_DATABASE, ensure_databases, make_engine
from extract import extract_batches
from load_raw import load_raw_batches, count_raw_run
from retrieve_raw import retrieve_batches
from transform import transform_batches
from validate import validate_data
from load_transformed import load_clean_batches, count_clean_run
from validate_report import write_reports


def run_pipeline():
    run_id = str(uuid4())
    raw_stats = {"successful_batches": 0, "failed_batches": [], "records_loaded": 0}
    clean_stats = None
    transform_stats = {}
    validation = {"passed": False, "errors": ["Pipeline did not reach validation"], "notes": [], "missing_values": {}}
    source_count = retrieved_count = 0
    rejected = pd.DataFrame()
    error_text = None
    try:
        print(f"Starting pipeline run {run_id}")
        ensure_databases()
        def counted_extraction():
            nonlocal source_count
            for item in extract_batches(CSV_PATH, BATCH_SIZE):
                source_count += len(item[2])
                yield item

        raw_engine = make_engine(RAW_DATABASE)
        try:
            raw_stats = load_raw_batches(raw_engine, counted_extraction(), run_id)
            if raw_stats["failed_batches"]:
                raise RuntimeError("One or more raw batches failed")
            retrieved = retrieve_batches(raw_engine, run_id, BATCH_SIZE)
            raw_db_count = count_raw_run(raw_engine, run_id)
        finally:
            raw_engine.dispose()
        retrieved_count = sum(len(batch) for batch in retrieved)
        if raw_db_count != source_count or retrieved_count != source_count:
            raise RuntimeError(f"Raw count verification failed: extracted={source_count}, in_raw_db={raw_db_count}, retrieved={retrieved_count}")
        clean_df, rejected, transform_stats = transform_batches(retrieved)
        validation = validate_data(clean_df, rejected)
        if not validation["passed"]:
            raise RuntimeError("Validation failed; analytics load was stopped")
        clean_engine = make_engine(ANALYTICS_DATABASE)
        try:
            clean_stats = load_clean_batches(clean_engine, clean_df, BATCH_SIZE)
            analytics_db_count = count_clean_run(clean_engine, run_id)
        finally:
            clean_engine.dispose()
        if clean_stats["failed_batches"]:
            raise RuntimeError("One or more analytics batches failed")
        if analytics_db_count != len(clean_df):
            raise RuntimeError(f"Analytics count verification failed: expected={len(clean_df)}, found={analytics_db_count}")
    except Exception as exc:
        error_text = str(exc)
        print(f"PIPELINE ERROR: {error_text}")
    finally:
        report_path, _ = write_reports(PROJECT_DIR, run_id, source_count, retrieved_count, transform_stats, validation, clean_stats, raw_stats, error_text)
        if not rejected.empty:
            rejected.to_csv(PROJECT_DIR / "reports" / f"rejected_records_{run_id}.csv", index=False)
        print(f"Validation report: {report_path}")
        print(f"Final status: {'PASSED' if error_text is None and validation.get('passed') else 'FAILED'}")
        print(f"Extraction batches: {(source_count + BATCH_SIZE - 1) // BATCH_SIZE}; retrieval batches: {(retrieved_count + BATCH_SIZE - 1) // BATCH_SIZE}")
        raw_ok = raw_stats.get("successful_batches", 0)
        raw_bad = len(raw_stats.get("failed_batches", []))
        clean_ok = (clean_stats or {}).get("successful_batches", 0)
        clean_bad = len((clean_stats or {}).get("failed_batches", []))
        print(f"Load batches successful: {raw_ok + clean_ok}; failed: {raw_bad + clean_bad}")
        print(f"Extracted={source_count}; raw_retrieved={retrieved_count}; valid={transform_stats.get('valid_records', 0)}; rejected={transform_stats.get('rejected_records', 0)}; analytics_loaded={(clean_stats or {}).get('records_loaded', 0)}")
    if error_text:
        raise SystemExit(1)


if __name__ == "__main__":
    run_pipeline()
