import pandas as pd
from sqlalchemy import text
from config import RAW_TABLE


def retrieve_batches(engine, run_id, batch_size=100):
    query = text(f"SELECT * FROM {RAW_TABLE} WHERE source_run_id = :run_id ORDER BY source_row_number")
    batches = []
    with engine.connect() as conn:
        for number, batch in enumerate(pd.read_sql_query(query, conn, params={"run_id": run_id}, chunksize=batch_size), start=1):
            batches.append(batch)
            print(f"Retrieve batch {number}: {len(batch)} records")
    return batches
