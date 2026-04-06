# analysis_readme.md — `ananlysis.py`

## Overview

`ananlysis.py` is the main analysis module for the DCPS2 transit cancellation project. It loads the three processed CSV files, cleans and enriches the data, runs a wide range of statistical analyses, and prints a human-readable summary to the console.

**Author:** Tyler Brady

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `numpy` | Vectorised operations, statistical functions |
| `pandas` | DataFrame loading and manipulation |
| `pathlib` | File path construction |

---

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DATA_DIR` | `../../data/processed/` | Root directory for processed CSV files |
| `ALL_CANCELLATIONS_FILE` | `all_cancellation_details.csv` | Detailed cancellation records |
| `BY_DAY_FILE` | `cancellations_by_day.csv` | Cancellations aggregated by day |
| `BY_ROUTE_FILE` | `cancellations_by_route.csv` | Cancellations aggregated by route |
| `WEEKDAYS` | Mon–Fri | frozenset used for vectorised weekday classification |
| `WEEKENDS` | Sat–Sun | frozenset used for vectorised weekend classification |
| `Z_SCORE_OUTLIER_THRESHOLD` | `3.0` | Z-score cutoff for anomaly detection |
| `HIGH_IMPACT_PERCENTILE` | `75` | Percentile threshold for high-impact route identification |

---

## Functions

### 1. `load_cancellation_data()`
Loads all three processed CSV files and returns them as a tuple of DataFrames `(details, by_day, by_route)`. Parses the `date` column as datetime.

---

### 2. `preprocess_data(details)`
Validates, cleans, and enriches the raw cancellation details DataFrame.
- Drops rows with nulls in `date`, `route_id`, or `day_of_week`.
- Adds `is_weekday` (bool) using `np.isin` — vectorised weekday classification.
- Adds `month`, `week`, and `year` columns from the `date` column.

**Returns:** enriched `pd.DataFrame`

---

### 3. `compare_weekday_weekend_cancellations(details)`
Compares total cancellation counts between weekdays and weekends using `np.sum` on a boolean array.

**Returns:** dict with `weekday_cancellations`, `weekend_cancellations`, `weekday_proportion`, `weekend_proportion`.

---

### 4. `get_top_10_most_cancelled(by_route)`
Returns the top-10 routes ranked by total cancelled trips. Uses `np.argpartition` for O(n) top-N selection.

**Returns:** `pd.DataFrame` (≤10 rows) with `route_short_name`, `route_long_name`, `total_cancelled_trips`.

---

### 5. `analyze_cancellation_by_route_category(details)`
Groups cancellation counts by the first character of `route_short_name`. Alphabetic characters represent lettered route families; numeric routes are grouped as `"Numeric"`. Uses `np.unique` for vectorised counting.

**Returns:** dict mapping category → count, sorted descending.

---

### 6. `calculate_route_efficiency(by_route)`
Calculates average daily cancellations per route using vectorised safe division via `np.where`.

**Returns:** `pd.DataFrame` with `avg_cancellations_per_day` and `total_cancelled_trips`, sorted descending.

---

### 7. `identify_high_impact_routes(by_route)`
Identifies routes at or above the 75th percentile of total cancellations using `np.percentile`. Adds a `percentile_rank` column.

**Returns:** `pd.DataFrame` of high-impact routes sorted descending.

---

### 8. `analyze_geographic_clustering(details)`
Clusters routes by letter-prefix to approximate geographic zones (Dublin Bus / Go-Ahead naming conventions). Uses `np.unique`.

**Returns:** dict mapping region → `{count, proportion}`.

---

### 9. `analyze_cancellation_trends_over_time(details)`
Computes weekly cancellation totals and a linear trend direction using `np.polyfit` (least-squares) and `np.cumsum` for running totals.

**Returns:** dict with `weekly_counts`, `cumulative_counts`, `slope`, and `trend` (`"increasing"` / `"decreasing"` / `"stable"`).

---

### 10. `correlate_exception_dates(details)`
Correlates exception-type codes with per-day cancellation volume using `np.corrcoef` (Pearson correlation).

**Returns:** dict with `exception_type_counts` and `correlation_with_day_volume`.

---

### 11. `analyze_seasonal_patterns(details)`
Summarises cancellations by calendar month. Applies `np.mean`, `np.median`, `np.std`, `np.argmax`, and `np.argmin`.

**Returns:** dict with `monthly_counts`, `mean`, `median`, `std`, `peak_month`, `quietest_month`.

---

### 12. `calculate_route_statistics(by_route)`
Computes a full descriptive-statistics profile across all routes: mean, median, std, min, max, Q25, Q75, IQR. Uses `np.percentile`.

**Returns:** dict with numerical summaries and `total_routes` / `total_cancellations`.

---

### 13. `calculate_correlation_with_route_length(by_route)`
Estimates Pearson correlation between route-name length (proxy for route complexity) and total cancellations using `np.corrcoef`.

**Returns:** dict with `correlation` and `interpretation` (`"positive"` / `"negative"` / `"negligible"`).

---

### 14. `analyze_agency_comparison(details)`
Compares cancellation volumes across agency IDs using z-score normalisation so agencies can be compared regardless of scale.

**Returns:** dict mapping `agency_id` → `{count, z_score}`.

---

### 15. `validate_data_integrity(details)`
Boundary validation — checks for missing required columns and null values in the loaded DataFrame.

**Returns:** dict with `total_rows`, `missing_required_columns`, `null_counts`, `total_null_values`, `is_valid`.

---

### 16. `verify_consistency(details, by_day, by_route)`
Cross-checks row/trip totals between the detailed and aggregated datasets. Flags discrepancies larger than a 5% relative tolerance.

**Returns:** dict with counts, deltas, and `day_consistent` / `route_consistent` flags.

---

### 17. `identify_data_anomalies(details)`
Flags routes whose cancellation count deviates beyond `Z_SCORE_OUTLIER_THRESHOLD` (z-score method). Implements the z-score anomaly detection pipeline.

**Returns:** dict with `anomalous_routes` list, `anomaly_count`, threshold, mean, and std.

---

### 18. `run_all_analyses(details, by_day, by_route)`
Orchestrates every analysis function and aggregates results into a single dict keyed by analysis name.

**Returns:** dict with keys: `data_integrity`, `consistency`, `anomalies`, `weekday_vs_weekend`, `top_10_routes`, `route_categories`, `route_efficiency`, `high_impact_routes`, `geographic_clustering`, `trends_over_time`, `exception_date_correlation`, `seasonal_patterns`, `route_statistics`, `route_length_correlation`, `agency_comparison`.

---

### 19. `print_summary(results)`
Prints a formatted console summary of the analysis results including route statistics, weekday vs weekend breakdown, trend direction, and anomaly count.

---

### 20. `main()`
Entry point. Calls `load_cancellation_data()` → `preprocess_data()` → `run_all_analyses()` → `print_summary()`.

**Returns:** full results dict (useful when called from notebooks or tests).

---

## Usage

```bash
python src/ananlysis.py
```

Or import individual functions:

```python
from src.ananlysis import load_cancellation_data, preprocess_data, run_all_analyses

details, by_day, by_route = load_cancellation_data()
details = preprocess_data(details)
results = run_all_analyses(details, by_day, by_route)
```

---

## Programming Principles Applied

- Vectorised operations over explicit Python loops wherever possible.
- NumPy ufuncs (`np.sqrt`, `np.abs`, `np.sum`) for element-wise work.
- Broadcasting to apply per-route corrections without looping.
- `np.corrcoef` / `np.polyfit` for statistical relationships.
- Z-score method for anomaly detection.
- `np.percentile` for robust thresholds rather than hard-coded magic numbers.
- `np.cumsum` for running totals.
- Boolean indexing for filtering; `np.where` / `np.isin` for conditional logic.

