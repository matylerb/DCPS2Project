# Processed Data

This folder contains the exported results from the data engineering pipeline.

## Files

- `cancellations_by_route.csv` / `.json` — Routes ranked by cancellation count
- `cancellations_by_day.csv` / `.json` — Cancellations by day of week
- `all_cancellation_details.csv` / `.json` — Full cancellation records with route info

## How to regenerate

Run the pipeline from the src folder:
```bash
cd src
python data_engineering.py
```

