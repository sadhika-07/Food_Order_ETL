# Source-data preflight report

Status: PRE-RUN SOURCE CHECK ONLY. This is not evidence that the MySQL pipeline has executed. Run elt_batch_pipeline.py after configuring MySQL to generate a run-specific validation report.

- Original records found in the CSV: 1,010
- Extraction batches at 100 rows: 11 (10 batches of 100 and a final batch of 10)
- Fully duplicated extra copies in source: 10
- Expected records after exact duplicate removal: 1,000
- Repeated Order IDs after exact duplicates are removed: 0
- Invalid timestamp pairs found in prior source assessment: 0
- Delivery-before-order records found: 0
- Negative financial values found: 0
- Missing financial values after exact duplicate removal: Order Value 40; Delivery Fee 50; Commission Fee 40; Payment Processing Fee 50; Refunds/Chargebacks 40. These remain missing by design and are not imputed as zero.
- Records with all four net-revenue components present: 828 of 1,000.

The execution-specific report will include actual MySQL batch counts, validation results, rejected records, and analytics insert counts.
