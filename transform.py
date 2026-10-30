import pandas as pd
import numpy as np
from config import RAW_COLUMNS

NUMERIC_MAP = {"Order Value": "order_value", "Delivery Fee": "delivery_fee", "Commission Fee": "commission_fee", "Payment Processing Fee": "payment_processing_fee", "Refunds/Chargebacks": "refunds_chargebacks"}
COLUMN_MAP = {"Order ID": "order_id", "Customer ID": "customer_id", "Restaurant ID": "restaurant_id", "Payment Method": "payment_method", "Discounts and Offers": "discounts_and_offers", "Weather Condition": "weather_condition", "Order Channel": "order_channel"}


def transform_batches(retrieved_batches):
    """Concatenate retrieved batches before deduping, so batch-boundary duplicates are found."""
    if not retrieved_batches:
        return pd.DataFrame(), pd.DataFrame(), {"input_records": 0, "valid_records": 0, "rejected_records": 0, "exact_duplicates": 0}
    source = pd.concat(retrieved_batches, ignore_index=True)
    exact_mask = source.duplicated(subset=RAW_COLUMNS, keep="first")
    rejected_parts = []
    exact = source.loc[exact_mask].copy()
    if not exact.empty:
        exact["rejection_reason"] = "exact_duplicate_copy"
        rejected_parts.append(exact)
    unique = source.loc[~exact_mask].copy().reset_index(drop=True)

    ids = unique["Order ID"].fillna("").astype(str).str.strip()
    conflict_mask = ids.ne("") & ids.duplicated(keep=False)
    conflicts = unique.loc[conflict_mask].copy()
    if not conflicts.empty:
        conflicts["rejection_reason"] = "repeated_order_id_conflict"
        rejected_parts.append(conflicts)
    candidates = unique.loc[~conflict_mask].copy().reset_index(drop=True)

    reasons = [[] for _ in range(len(candidates))]
    orders = pd.to_datetime(candidates["Order Date and Time"], errors="coerce")
    deliveries = pd.to_datetime(candidates["Delivery Date and Time"], errors="coerce")
    for i in np.flatnonzero(orders.isna().to_numpy()):
        reasons[i].append("invalid_or_missing_order_timestamp")
    for i in np.flatnonzero(deliveries.isna().to_numpy()):
        reasons[i].append("invalid_or_missing_delivery_timestamp")

    numbers = {}
    for original, target in NUMERIC_MAP.items():
        text_values = candidates[original].fillna("").astype(str).str.strip()
        parsed = pd.to_numeric(text_values.replace("", np.nan), errors="coerce")
        bad = text_values.ne("") & parsed.isna()
        for i in np.flatnonzero(bad.to_numpy()):
            reasons[i].append(f"invalid_numeric_{target}")
        for i in np.flatnonzero((parsed < 0).fillna(False).to_numpy()):
            reasons[i].append(f"negative_financial_{target}")
        numbers[target] = parsed

    duration = (deliveries - orders).dt.total_seconds() / 60
    for i in np.flatnonzero((duration < 0).fillna(False).to_numpy()):
        reasons[i].append("negative_delivery_duration")
    reason_series = pd.Series([";".join(r) for r in reasons])
    invalid = reason_series.ne("")
    invalid_rows = candidates.loc[invalid].copy()
    if not invalid_rows.empty:
        invalid_rows["rejection_reason"] = reason_series.loc[invalid].values
        rejected_parts.append(invalid_rows)

    keep = ~invalid
    valid = candidates.loc[keep].reset_index(drop=True)
    valid_orders = orders.loc[keep].reset_index(drop=True)
    valid_deliveries = deliveries.loc[keep].reset_index(drop=True)
    result = pd.DataFrame()
    result["source_run_id"] = valid["source_run_id"].astype(str)
    result["source_row_number"] = pd.to_numeric(valid["source_row_number"], errors="raise").astype("int64")
    for src, target in COLUMN_MAP.items():
        result[target] = valid[src].fillna("").astype(str).str.strip()
    result["order_datetime"] = valid_orders
    result["delivery_datetime"] = valid_deliveries
    for target, values in numbers.items():
        result[target] = values.loc[keep].reset_index(drop=True)
    result["delivery_time_minutes"] = (valid_deliveries - valid_orders).dt.total_seconds() / 60
    result["order_date"] = valid_orders.dt.date
    result["order_hour"] = valid_orders.dt.hour.astype("int64")
    components = ["commission_fee", "delivery_fee", "payment_processing_fee", "refunds_chargebacks"]
    complete = result[components].notna().all(axis=1)
    result["platform_net_revenue"] = np.nan
    result.loc[complete, "platform_net_revenue"] = result.loc[complete, "commission_fee"] + result.loc[complete, "delivery_fee"] - result.loc[complete, "payment_processing_fee"] - result.loc[complete, "refunds_chargebacks"]
    result["payment_method"] = result["payment_method"].replace("", "Unknown")
    result["discounts_and_offers"] = result["discounts_and_offers"].replace("", "Not Specified")
    rejected = pd.concat(rejected_parts, ignore_index=True) if rejected_parts else pd.DataFrame()
    stats = {"input_records": len(source), "exact_duplicates": int(exact_mask.sum()), "repeated_order_id_conflicts": int(conflict_mask.sum()), "invalid_timestamp_or_value_records": int(invalid.sum()), "valid_records": len(result), "rejected_records": len(rejected), "revenue_records_with_all_components": int(complete.sum())}
    return result, rejected, stats
