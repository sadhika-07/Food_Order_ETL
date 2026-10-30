from pathlib import Path
import json
import pandas as pd


def write_reports(project_dir, run_id, source_count, retrieved_count, transform_stats, validation, load_stats, raw_stats, error=None):
    reports = Path(project_dir) / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    md_path = reports / f"validation_report_{run_id}.md"
    json_path = reports / f"execution_report_{run_id}.json"
    payload = {"run_id": run_id, "source_records": source_count, "raw_records_retrieved": retrieved_count, "transform": transform_stats, "validation": validation, "raw_load": raw_stats, "analytics_load": load_stats, "pipeline_error": error}
    lines = [f"# ELT Validation and Execution Report — {run_id}", "", f"- Source records extracted: {source_count}", f"- Raw records loaded: {raw_stats.get('records_loaded', 0)}", f"- Raw records retrieved: {retrieved_count}", f"- Exact duplicate copies identified: {transform_stats.get('exact_duplicates', 0)}", f"- Valid transformed records: {transform_stats.get('valid_records', 0)}", f"- Rejected records: {transform_stats.get('rejected_records', 0)}", f"- Records with complete revenue inputs: {transform_stats.get('revenue_records_with_all_components', 0)}", f"- Analytics records loaded: {(load_stats or {}).get('records_loaded', 0)}", f"- Validation status: {'PASSED' if validation.get('passed') else 'FAILED'}", f"- Overall pipeline status: {'FAILED' if error else ('PASSED' if validation.get('passed') else 'FAILED')}", f"- Extraction/retrieval batches (at 100 rows): {(source_count + 99) // 100} / {(retrieved_count + 99) // 100}", f"- Total batches attempted across load stages: {raw_stats.get('successful_batches', 0) + len(raw_stats.get('failed_batches', [])) + (load_stats or {}).get('successful_batches', 0) + len((load_stats or {}).get('failed_batches', []))}", f"- Successful raw batches: {raw_stats.get('successful_batches', 0)}", f"- Failed raw batches: {len(raw_stats.get('failed_batches', []))}", f"- Successful analytics batches: {(load_stats or {}).get('successful_batches', 0)}", f"- Failed analytics batches: {len((load_stats or {}).get('failed_batches', []))}"]
    if error: lines += [f"- Pipeline error: {error}"]
    lines += ["", "## Missing values in cleaned data", "", pd.Series(validation.get("missing_values", {}), name="missing_count").to_frame().to_markdown(), "", "## Validation notes", ""]
    lines += [f"- {note}" for note in validation.get("notes", [])]
    if validation.get("errors"):
        lines += ["", "## Validation errors", ""] + [f"- {e}" for e in validation["errors"]]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return md_path, json_path
