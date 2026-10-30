import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

EXPECTED = ["source_run_id", "source_row_number", "order_id", "customer_id", "restaurant_id", "order_datetime", "delivery_datetime", "order_value", "delivery_fee", "payment_method", "discounts_and_offers", "commission_fee", "payment_processing_fee", "refunds_chargebacks", "weather_condition", "order_channel", "delivery_time_minutes", "order_date", "order_hour", "platform_net_revenue"]


def validate_data(clean_df, rejected_df):
    errors, notes = [], []
    missing_cols = [c for c in EXPECTED if c not in clean_df.columns]
    if missing_cols:
        return {"passed": False, "errors": [f"Missing columns: {missing_cols}"], "notes": [], "missing_values": {}}
    if clean_df.duplicated().any():
        errors.append(f"Duplicate cleaned rows: {int(clean_df.duplicated().sum())}")
    if clean_df["order_id"].duplicated().any():
        errors.append("Repeated order_id values remain")
    if clean_df["delivery_time_minutes"].lt(0).any():
        errors.append("Negative delivery durations remain")
    if clean_df[["order_datetime", "delivery_datetime"]].isna().any().any():
        errors.append("Null timestamp remains in valid records")
    if not all(is_datetime64_any_dtype(clean_df[c]) for c in ["order_datetime", "delivery_datetime"]):
        errors.append("Datetime dtype check failed")
    numeric = ["order_value", "delivery_fee", "commission_fee", "payment_processing_fee", "refunds_chargebacks", "delivery_time_minutes", "platform_net_revenue"]
    if not all(is_numeric_dtype(clean_df[c]) for c in numeric):
        errors.append("Numeric dtype check failed")
    components = ["commission_fee", "delivery_fee", "payment_processing_fee", "refunds_chargebacks"]
    complete = clean_df[components].notna().all(axis=1)
    calculated = clean_df["commission_fee"] + clean_df["delivery_fee"] - clean_df["payment_processing_fee"] - clean_df["refunds_chargebacks"]
    if not np.isclose(clean_df.loc[complete, "platform_net_revenue"], calculated.loc[complete]).all():
        errors.append("Revenue formula validation failed")
    if clean_df.loc[~complete, "platform_net_revenue"].notna().any():
        errors.append("Revenue exists despite missing formula input")
    missing = clean_df.isna().sum().astype(int).to_dict()
    notes.append("Missing financial values remain NULL by rule and are excluded from calculations requiring them.")
    notes.append(f"Rejected rows are recorded separately: {len(rejected_df)}.")
    return {"passed": not errors, "errors": errors, "notes": notes, "missing_values": missing, "records_valid": len(clean_df), "records_rejected": len(rejected_df)}
