import pandas as pd
from sqlalchemy import Column, Date, DateTime, Integer, MetaData, Numeric, String, Table, insert, select, func
from config import CLEAN_TABLE

metadata = MetaData()
clean_table = Table(CLEAN_TABLE, metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_run_id", String(36), nullable=False, index=True), Column("source_row_number", Integer, nullable=False),
    Column("order_id", String(50), nullable=False), Column("customer_id", String(50)), Column("restaurant_id", String(50)),
    Column("order_datetime", DateTime, nullable=False), Column("delivery_datetime", DateTime, nullable=False),
    Column("order_value", Numeric(12, 2)), Column("delivery_fee", Numeric(12, 2)),
    Column("payment_method", String(100), nullable=False), Column("discounts_and_offers", String(255), nullable=False),
    Column("commission_fee", Numeric(12, 2)), Column("payment_processing_fee", Numeric(12, 2)), Column("refunds_chargebacks", Numeric(12, 2)),
    Column("weather_condition", String(50)), Column("order_channel", String(50)), Column("delivery_time_minutes", Numeric(10, 2), nullable=False),
    Column("order_date", Date, nullable=False), Column("order_hour", Integer, nullable=False), Column("platform_net_revenue", Numeric(12, 2)))


def _records(frame):
    out = []
    for row in frame.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            if pd.isna(value): clean[key] = None
            elif isinstance(value, pd.Timestamp): clean[key] = value.to_pydatetime()
            elif hasattr(value, "item"): clean[key] = value.item()
            else: clean[key] = value
        out.append(clean)
    return out


def load_clean_batches(engine, clean_df, batch_size=100):
    metadata.create_all(engine)
    success, failures, total = 0, [], 0
    for batch_no, start in enumerate(range(0, len(clean_df), batch_size), start=1):
        frame = clean_df.iloc[start:start + batch_size]
        try:
            with engine.begin() as conn:
                conn.execute(insert(clean_table), _records(frame))
            success += 1
            total += len(frame)
            print(f"Analytics load batch {batch_no}: committed {len(frame)} records")
        except Exception as exc:
            failures.append({"batch_number": batch_no, "error": str(exc)})
            print(f"Analytics batch {batch_no} failed and rolled back: {exc}")
            break
    return {"successful_batches": success, "failed_batches": failures, "records_loaded": total}


def count_clean_run(engine, run_id):
    with engine.connect() as conn:
        return int(conn.execute(select(func.count()).select_from(clean_table).where(clean_table.c.source_run_id == run_id)).scalar_one())
