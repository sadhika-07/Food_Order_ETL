import pandas as pd
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, select, func
from config import RAW_COLUMNS, RAW_TABLE

metadata = MetaData()
raw_table = Table(RAW_TABLE, metadata, *[Column(c, Text(), nullable=True) for c in RAW_COLUMNS], Column("source_run_id", String(36), nullable=False, index=True), Column("source_batch_number", Integer, nullable=False), Column("source_row_number", Integer, nullable=False), Column("loaded_at_utc", DateTime, nullable=False))
batch_log = Table("raw_batch_log", metadata, Column("source_run_id", String(36), primary_key=True), Column("batch_number", Integer, primary_key=True), Column("record_count", Integer, nullable=False))


def load_raw_batches(engine, batches, run_id):
    metadata.create_all(engine)
    successful, failed, total = 0, [], 0
    for batch_number, row_offset, batch in batches:
        records = batch.to_dict(orient="records")
        loaded_at = pd.Timestamp.utcnow().to_pydatetime().replace(tzinfo=None)
        for i, row in enumerate(records):
            row.update({"source_run_id": run_id, "source_batch_number": batch_number, "source_row_number": row_offset + i + 1, "loaded_at_utc": loaded_at})
        try:
            with engine.begin() as conn:
                exists = conn.execute(select(batch_log.c.batch_number).where(batch_log.c.source_run_id == run_id, batch_log.c.batch_number == batch_number)).first()
                if exists:
                    raise RuntimeError("This run/batch is already loaded; refusing to append it twice.")
                conn.execute(raw_table.insert(), records)
                conn.execute(batch_log.insert().values(source_run_id=run_id, batch_number=batch_number, record_count=len(batch)))
            successful += 1
            total += len(batch)
            print(f"Raw load batch {batch_number}: committed {len(batch)} records")
        except Exception as exc:
            failed.append({"batch_number": batch_number, "error": str(exc)})
            print(f"Raw batch {batch_number} failed and rolled back: {exc}")
    return {"successful_batches": successful, "failed_batches": failed, "records_loaded": total}


def count_raw_run(engine, run_id):
    with engine.connect() as conn:
        return int(conn.execute(select(func.count()).select_from(raw_table).where(raw_table.c.source_run_id == run_id)).scalar_one())
