# ELT Validation and Execution Report — 3f37f7bb-6bf8-4fc8-81c6-3a094a775cdf

- Source records extracted: 1010
- Raw records loaded: 1010
- Raw records retrieved: 1010
- Exact duplicate copies identified: 10
- Valid transformed records: 1000
- Rejected records: 10
- Records with complete revenue inputs: 828
- Analytics records loaded: 1000
- Validation status: PASSED
- Overall pipeline status: PASSED
- Extraction/retrieval batches (at 100 rows): 11 / 11
- Total batches attempted across load stages: 21
- Successful raw batches: 11
- Failed raw batches: 0
- Successful analytics batches: 10
- Failed analytics batches: 0

## Missing values in cleaned data

|                        |   missing_count |
|:-----------------------|----------------:|
| source_run_id          |               0 |
| source_row_number      |               0 |
| order_id               |               0 |
| customer_id            |               0 |
| restaurant_id          |               0 |
| payment_method         |               0 |
| discounts_and_offers   |               0 |
| weather_condition      |               0 |
| order_channel          |               0 |
| order_datetime         |               0 |
| delivery_datetime      |               0 |
| order_value            |              40 |
| delivery_fee           |              50 |
| commission_fee         |              40 |
| payment_processing_fee |              50 |
| refunds_chargebacks    |              40 |
| delivery_time_minutes  |               0 |
| order_date             |               0 |
| order_hour             |               0 |
| platform_net_revenue   |             172 |

## Validation notes

- Missing financial values remain NULL by rule and are excluded from calculations requiring them.
- Rejected rows are recorded separately: 10.
