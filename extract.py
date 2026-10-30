import pandas as pd
from config import BATCH_SIZE, CSV_PATH, RAW_COLUMNS


def extract_batches(csv_path=CSV_PATH, batch_size=BATCH_SIZE):
    """Read CSV values unchanged and yield batches; no cleaning or type conversion."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    offset = 0
    for batch_number, batch in enumerate(pd.read_csv(csv_path, dtype=str, keep_default_na=False, encoding="utf-8-sig", chunksize=batch_size), start=1):
        if list(batch.columns) != RAW_COLUMNS:
            raise ValueError(f"Unexpected source columns: {list(batch.columns)}")
        print(f"Extract batch {batch_number}: {len(batch)} records")
        yield batch_number, offset, batch
        offset += len(batch)
