"""
data_analysis.py
===============

Program Description: A detailed analysis module for DCPS2 transit cancellation data, applying a wide range of data analysis techniques and principles.
Author: Tyler Brady
===============


Programming principles applied:
  - Vectorised operations over explicit Python loops wherever possible.
  - NumPy ufuncs (np.sqrt, np.abs, np.sum, …) for element-wise work.
  - Broadcasting to apply per-route corrections without looping.
  - np.corrcoef / np.polyfit for statistical relationships.
  - Z-score method (Lecture 5) for anomaly detection.
  - np.percentile for robust thresholds rather than hard-coded magic numbers.
  - np.cumsum for running totals (energy-monitoring pattern from Lecture 5).
  - Boolean indexing for filtering; np.where / np.isin for conditional logic.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
ALL_CANCELLATIONS_FILE = DATA_DIR / "all_cancellation_details.csv"
BY_DAY_FILE = DATA_DIR / "cancellations_by_day.csv"
BY_ROUTE_FILE = DATA_DIR / "cancellations_by_route.csv"

WEEKDAYS = frozenset({"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"})
WEEKENDS = frozenset({"Saturday", "Sunday"})

Z_SCORE_OUTLIER_THRESHOLD = 3.0
HIGH_IMPACT_PERCENTILE = 75


# ---------------------------------------------------------------------------
# 1. load_cancellation_data
# ---------------------------------------------------------------------------
def load_cancellation_data():
    """Load all three processed cancellation CSV files.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        (details, by_day, by_route)
    """
    details = pd.read_csv(ALL_CANCELLATIONS_FILE, parse_dates=["date"])
    by_day = pd.read_csv(BY_DAY_FILE)
    by_route = pd.read_csv(BY_ROUTE_FILE)
    return details, by_day, by_route


# ---------------------------------------------------------------------------
# 2. preprocess_data
# ---------------------------------------------------------------------------
def preprocess_data(details):
    """Validate, clean, and enrich the raw cancellation details DataFrame.

    Uses np.isin for vectorised weekday classification instead of row-wise
    Python comparisons.

    Parameters
    ----------
    details : pd.DataFrame

    Returns
    -------
    pd.DataFrame with added columns: is_weekday, month, week, year.
    """
    details = details.dropna(subset=["date", "route_id", "day_of_week"]).copy()

    # Vectorised weekday flag (Lecture 4 – Boolean indexing)
    details["is_weekday"] = np.isin(
        details["day_of_week"].values, list(WEEKDAYS)
    )
    details["month"] = details["date"].dt.month
    details["week"] = details["date"].dt.isocalendar().week.astype(int)
    details["year"] = details["date"].dt.year

    return details


# ---------------------------------------------------------------------------
# 3. compare_weekday_weekend_cancellations
# ---------------------------------------------------------------------------
def compare_weekday_weekend_cancellations(details):
    """Compare total cancellation counts between weekdays and weekends.

    Uses np.sum on a boolean array – vectorised reduction (Lecture 4).

    Parameters
    ----------
    details : pd.DataFrame  (must contain `is_weekday` column)

    Returns
    -------
    dict with weekday/weekend counts and proportions.
    """
    is_weekday = details["is_weekday"].values
    counts = np.array([np.sum(is_weekday), np.sum(~is_weekday)], dtype=np.int64)
    total = counts.sum()
    proportions = counts / total if total > 0 else np.zeros(2)

    return {
        "weekday_cancellations": int(counts[0]),
        "weekend_cancellations": int(counts[1]),
        "weekday_proportion": float(proportions[0]),
        "weekend_proportion": float(proportions[1]),
    }


# ---------------------------------------------------------------------------
# 4. get_top_10_most_cancelled
# ---------------------------------------------------------------------------
def get_top_10_most_cancelled(by_route):
    """Return the top-10 routes ranked by total cancelled trips.

    Uses np.argpartition for O(n) top-N selection rather than full sort
    (Lecture 4 – choose the appropriate paradigm).

    Parameters
    ----------
    by_route : pd.DataFrame

    Returns
    -------
    pd.DataFrame (≤10 rows), sorted descending.
    """
    total = by_route["total_cancelled_trips"].values

    if len(total) <= 10:
        top_idx = np.argsort(total)[::-1]
    else:
        part_idx = np.argpartition(total, -10)[-10:]
        top_idx = part_idx[np.argsort(total[part_idx])[::-1]]

    return (
        by_route.iloc[top_idx][
            ["route_short_name", "route_long_name", "total_cancelled_trips"]
        ]
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# 5. analyze_cancellation_by_route_category
# ---------------------------------------------------------------------------
def analyze_cancellation_by_route_category(details):
    """Group cancellation counts by the first character of route_short_name.

    Alphabetic first characters represent lettered route families (e.g. 'S',
    'N', 'W'); purely numeric routes are grouped as 'Numeric'.

    Uses np.unique for vectorised counting (Lecture 4).

    Parameters
    ----------
    details : pd.DataFrame

    Returns
    -------
    dict mapping category → count, sorted descending.
    """
    short_names = details["route_short_name"].fillna("Unknown").values

    def _category(name):
        return name[0].upper() if name and name[0].isalpha() else "Numeric"

    categories = np.array([_category(n) for n in short_names])
    unique_cats, counts = np.unique(categories, return_counts=True)
    order = np.argsort(counts)[::-1]

    return dict(zip(unique_cats[order].tolist(), counts[order].tolist()))


# ---------------------------------------------------------------------------
# 6. calculate_route_efficiency
# ---------------------------------------------------------------------------
def calculate_route_efficiency(by_route):
    """Calculate average daily cancellations per route.

    Uses np.where for vectorised zero-safe division (Lecture 4 – broadcasting).

    Parameters
    ----------
    by_route : pd.DataFrame

    Returns
    -------
    pd.DataFrame with avg_cancellations_per_day, sorted descending.
    """
    total = by_route["total_cancelled_trips"].values.astype(float)
    dates = by_route["cancelled_dates"].values.astype(float)

    # Vectorised safe division
    avg = np.where(dates > 0, total / dates, 0.0)

    result = by_route[["route_short_name", "route_long_name"]].copy()
    result["avg_cancellations_per_day"] = avg
    result["total_cancelled_trips"] = total.astype(int)

    return result.sort_values("avg_cancellations_per_day", ascending=False).reset_index(
        drop=True
    )


# ---------------------------------------------------------------------------
# 7. identify_high_impact_routes
# ---------------------------------------------------------------------------
def identify_high_impact_routes(by_route):
    """Identify routes whose cancellations are at or above the 75th percentile.

    Uses np.percentile for a robust, distribution-aware threshold
    (Lecture 5 – percentiles).

    Parameters
    ----------
    by_route : pd.DataFrame

    Returns
    -------
    pd.DataFrame of high-impact routes with a percentile_rank column.
    """
    total = by_route["total_cancelled_trips"].values.astype(float)
    threshold = np.percentile(total, HIGH_IMPACT_PERCENTILE)
    mask = total >= threshold

    high_impact = by_route[mask].copy()
    sorted_total = np.sort(total)
    high_impact["percentile_rank"] = np.round(
        (np.searchsorted(sorted_total, total[mask]) / len(total)) * 100, 1
    )

    return high_impact.sort_values("total_cancelled_trips", ascending=False).reset_index(
        drop=True
    )


# ---------------------------------------------------------------------------
# 8. analyze_geographic_clustering
# ---------------------------------------------------------------------------
def analyze_geographic_clustering(details):
    """Cluster routes by letter-prefix to approximate geographic zones.

    Alphabetic prefixes in Dublin Bus / Go-Ahead naming conventions roughly
    correspond to geographic corridors.  Uses np.unique (Lecture 4).

    Parameters
    ----------
    details : pd.DataFrame

    Returns
    -------
    dict mapping region → {count, proportion}.
    """
    names = details["route_short_name"].fillna("Unknown").values

    def _region(name):
        if not name or name == "Unknown":
            return "Unknown"
        return name[0].upper() if name[0].isalpha() else "Core"

    regions = np.array([_region(n) for n in names])
    unique_regions, counts = np.unique(regions, return_counts=True)
    proportions = counts / counts.sum()

    return {
        region: {"count": int(c), "proportion": round(float(p), 4)}
        for region, c, p in zip(unique_regions, counts, proportions)
    }


# ---------------------------------------------------------------------------
# 9. analyze_cancellation_trends_over_time
# ---------------------------------------------------------------------------
def analyze_cancellation_trends_over_time(details):
    """Compute weekly cancellation totals and a linear trend direction.

    Uses np.polyfit (vectorised least-squares, Lecture 5) and np.cumsum
    for running totals (Lecture 5 – cumulative operations).

    Parameters
    ----------
    details : pd.DataFrame  (must contain `year` and `week` columns)

    Returns
    -------
    dict with weekly_counts, cumulative_counts, slope, and trend label.
    """
    weekly = details.groupby(["year", "week"]).size().reset_index(name="count")
    counts = weekly["count"].values.astype(float)

    if len(counts) < 2:
        return {"weekly_counts": counts.tolist(), "trend": "insufficient_data"}

    x = np.arange(len(counts), dtype=float)
    slope, _ = np.polyfit(x, counts, 1)
    trend = "increasing" if slope > 0 else ("decreasing" if slope < 0 else "stable")

    return {
        "weekly_counts": counts.tolist(),
        "cumulative_counts": np.cumsum(counts).tolist(),
        "slope": float(slope),
        "trend": trend,
    }


# ---------------------------------------------------------------------------
# 10. correlate_exception_dates
# ---------------------------------------------------------------------------
def correlate_exception_dates(details):
    """Correlate exception_type codes with per-day cancellation volume.

    Uses np.corrcoef (Lecture 5 – Pearson correlation coefficient).

    Parameters
    ----------
    details : pd.DataFrame

    Returns
    -------
    dict with exception type counts and correlation coefficient.
    """
    exception_types = details["exception_type"].values.astype(float)
    day_counts = details.groupby("day_of_week").size().to_dict()

    # Vectorised mapping of each row to its day's total volume
    day_volumes = np.array(
        [day_counts.get(d, 0) for d in details["day_of_week"].values], dtype=float
    )

    if (
        len(exception_types) > 1
        and np.std(exception_types) > 0
        and np.std(day_volumes) > 0
    ):
        corr = float(np.corrcoef(exception_types, day_volumes)[0, 1])
    else:
        corr = 0.0

    unique_types, type_counts = np.unique(exception_types.astype(int), return_counts=True)

    return {
        "exception_type_counts": dict(
            zip(unique_types.tolist(), type_counts.tolist())
        ),
        "correlation_with_day_volume": corr,
    }


# ---------------------------------------------------------------------------
# 11. analyze_seasonal_patterns
# ---------------------------------------------------------------------------
def analyze_seasonal_patterns(details):
    """Summarise cancellations by calendar month.

    Applies np.mean / np.median / np.std / np.argmax (Lecture 5 – descriptive
    statistics).

    Parameters
    ----------
    details : pd.DataFrame  (must contain `month` column)

    Returns
    -------
    dict with monthly counts and summary statistics.
    """
    monthly_series = details.groupby("month").size()
    months = monthly_series.index.values
    counts = monthly_series.values.astype(float)

    if len(counts) == 0:
        return {}

    return {
        "monthly_counts": dict(zip(months.tolist(), counts.astype(int).tolist())),
        "mean": float(np.mean(counts)),
        "median": float(np.median(counts)),
        "std": float(np.std(counts)),
        "peak_month": int(months[np.argmax(counts)]),
        "quietest_month": int(months[np.argmin(counts)]),
    }


# ---------------------------------------------------------------------------
# 12. calculate_route_statistics
# ---------------------------------------------------------------------------
def calculate_route_statistics(by_route):
    """Compute a full descriptive-statistics profile across all routes.

    Applies mean, median, std, min, max, percentiles, IQR (Lecture 5 –
    complete statistical summary).

    Parameters
    ----------
    by_route : pd.DataFrame

    Returns
    -------
    dict with numerical summaries.
    """
    total = by_route["total_cancelled_trips"].values.astype(float)
    q25, q75 = np.percentile(total, [25, 75])

    return {
        "mean": float(np.mean(total)),
        "median": float(np.median(total)),
        "std": float(np.std(total)),
        "min": float(np.min(total)),
        "max": float(np.max(total)),
        "q25": float(q25),
        "q75": float(q75),
        "iqr": float(q75 - q25),
        "total_routes": int(len(total)),
        "total_cancellations": int(np.sum(total)),
    }


# ---------------------------------------------------------------------------
# 13. calculate_correlation_with_route_length
# ---------------------------------------------------------------------------
def calculate_correlation_with_route_length(by_route):
    """Estimate Pearson correlation between route-name length and cancellation count.

    Route name length is used as a proxy for route complexity / distance
    in the absence of geographic coordinates.

    Uses np.corrcoef (Lecture 5).

    Parameters
    ----------
    by_route : pd.DataFrame

    Returns
    -------
    dict with correlation value and interpretation label.
    """
    lengths = np.array(
        [len(n) for n in by_route["route_long_name"].fillna("").values], dtype=float
    )
    total = by_route["total_cancelled_trips"].values.astype(float)

    if len(lengths) < 2 or np.std(lengths) == 0 or np.std(total) == 0:
        return {"correlation": 0.0, "note": "insufficient_variance"}

    corr = float(np.corrcoef(lengths, total)[0, 1])
    interpretation = (
        "positive" if corr > 0.3 else ("negative" if corr < -0.3 else "negligible")
    )

    return {"correlation": corr, "interpretation": interpretation}


# ---------------------------------------------------------------------------
# 14. analyze_agency_comparison
# ---------------------------------------------------------------------------
def analyze_agency_comparison(details):
    """Compare cancellation volumes across agency IDs using z-score normalisation.

    Z-score normalisation (Lecture 5 – z-score calibration and normalisation)
    lets agencies be compared relative to the mean regardless of scale.

    Parameters
    ----------
    details : pd.DataFrame

    Returns
    -------
    dict mapping agency_id → {count, z_score}.
    """
    if "agency_id" not in details.columns:
        return {}

    agency_series = details.groupby("agency_id").size()
    counts = agency_series.values.astype(float)
    agencies = agency_series.index.values

    mean, std = np.mean(counts), np.std(counts)
    z_scores = (counts - mean) / std if std > 0 else np.zeros_like(counts)

    return {
        str(agency): {"count": int(c), "z_score": round(float(z), 4)}
        for agency, c, z in zip(agencies, counts.astype(int), z_scores)
    }


# ---------------------------------------------------------------------------
# 15. validate_data_integrity
# ---------------------------------------------------------------------------
def validate_data_integrity(details):
    """Check for missing required columns and null values.

    Boundary validation at the system boundary (inputs from CSV files).

    Parameters
    ----------
    details : pd.DataFrame

    Returns
    -------
    dict summarising integrity issues.
    """
    required = ["date", "route_id", "day_of_week", "route_short_name", "agency_id"]
    missing_cols = [c for c in required if c not in details.columns]

    null_counts = {col: int(details[col].isna().sum()) for col in details.columns}
    total_nulls = int(sum(null_counts.values()))

    return {
        "total_rows": int(len(details)),
        "missing_required_columns": missing_cols,
        "null_counts": null_counts,
        "total_null_values": total_nulls,
        "is_valid": len(missing_cols) == 0 and total_nulls == 0,
    }


# ---------------------------------------------------------------------------
# 16. verify_consistency
# ---------------------------------------------------------------------------
def verify_consistency(details, by_day, by_route):
    """Cross-check totals between the detailed and aggregated datasets.

    Flags large discrepancies that suggest data pipeline issues.

    Parameters
    ----------
    details : pd.DataFrame
    by_day : pd.DataFrame
    by_route : pd.DataFrame

    Returns
    -------
    dict with counts, deltas, and consistency flags.
    """
    detail_total = len(details)
    by_day_total = int(by_day["cancelled_trips"].sum())
    by_route_total = int(by_route["total_cancelled_trips"].sum())

    tolerance = 0.05  # 5 % relative tolerance
    day_delta = abs(detail_total - by_day_total)
    route_delta = abs(detail_total - by_route_total)

    return {
        "details_row_count": detail_total,
        "by_day_sum": by_day_total,
        "by_route_sum": by_route_total,
        "day_delta": day_delta,
        "route_delta": route_delta,
        "day_consistent": day_delta / max(detail_total, 1) <= tolerance,
        "route_consistent": route_delta / max(detail_total, 1) <= tolerance,
    }


# ---------------------------------------------------------------------------
# 17. identify_data_anomalies
# ---------------------------------------------------------------------------
def identify_data_anomalies(details):
    """Flag routes whose cancellation count deviates beyond Z_SCORE_OUTLIER_THRESHOLD.

    Implements the z-score anomaly detection pipeline from Lecture 5:
      z = (x - mean) / std ; flag where |z| > threshold.

    Parameters
    ----------
    details : pd.DataFrame

    Returns
    -------
    dict with list of anomalous routes and summary statistics.
    """
    route_counts = details.groupby("route_id").size()
    counts = route_counts.values.astype(float)

    if len(counts) < 2:
        return {
            "anomalous_routes": [],
            "anomaly_count": 0,
            "z_score_threshold": Z_SCORE_OUTLIER_THRESHOLD,
        }

    mean, std = float(np.mean(counts)), float(np.std(counts))
    z_scores = np.abs((counts - mean) / std) if std > 0 else np.zeros_like(counts)
    anomaly_mask = z_scores > Z_SCORE_OUTLIER_THRESHOLD

    anomalous = [
        {"route_id": rid, "count": int(c), "z_score": round(float(z), 3)}
        for rid, c, z in zip(
            route_counts.index[anomaly_mask],
            counts[anomaly_mask],
            z_scores[anomaly_mask],
        )
    ]

    return {
        "anomalous_routes": anomalous,
        "anomaly_count": len(anomalous),
        "z_score_threshold": Z_SCORE_OUTLIER_THRESHOLD,
        "mean_cancellations_per_route": mean,
        "std_cancellations_per_route": std,
    }


# ---------------------------------------------------------------------------
# 18. run_all_analyses
# ---------------------------------------------------------------------------
def run_all_analyses(details, by_day, by_route):
    """Execute every analysis function and aggregate results into one dict.

    Parameters
    ----------
    details : pd.DataFrame  (preprocessed)
    by_day : pd.DataFrame
    by_route : pd.DataFrame

    Returns
    -------
    dict keyed by analysis name.
    """
    return {
        "data_integrity": validate_data_integrity(details),
        "consistency": verify_consistency(details, by_day, by_route),
        "anomalies": identify_data_anomalies(details),
        "weekday_vs_weekend": compare_weekday_weekend_cancellations(details),
        "top_10_routes": get_top_10_most_cancelled(by_route).to_dict(orient="records"),
        "route_categories": analyze_cancellation_by_route_category(details),
        "route_efficiency": calculate_route_efficiency(by_route).to_dict(orient="records"),
        "high_impact_routes": identify_high_impact_routes(by_route).to_dict(orient="records"),
        "geographic_clustering": analyze_geographic_clustering(details),
        "trends_over_time": analyze_cancellation_trends_over_time(details),
        "exception_date_correlation": correlate_exception_dates(details),
        "seasonal_patterns": analyze_seasonal_patterns(details),
        "route_statistics": calculate_route_statistics(by_route),
        "route_length_correlation": calculate_correlation_with_route_length(by_route),
        "agency_comparison": analyze_agency_comparison(details),
    }


# ---------------------------------------------------------------------------
# 19. print_summary
# ---------------------------------------------------------------------------
def print_summary(results):
    """Print a human-readable console summary of the analysis results.

    Parameters
    ----------
    results : dict  (as returned by run_all_analyses)
    """
    stats = results.get("route_statistics", {})
    wkd = results.get("weekday_vs_weekend", {})
    trends = results.get("trends_over_time", {})
    integrity = results.get("data_integrity", {})
    anomalies = results.get("anomalies", {})

    print("=" * 60)
    print("DCPS2 Cancellation Analysis Summary")
    print("=" * 60)
    print(f"Total rows analysed  : {integrity.get('total_rows', 'N/A')}")
    print(f"Data valid           : {integrity.get('is_valid', 'N/A')}")
    print(f"Null values          : {integrity.get('total_null_values', 'N/A')}")
    print()
    print("--- Route Statistics ---")
    print(f"  Total routes       : {stats.get('total_routes', 'N/A')}")
    print(f"  Total cancellations: {stats.get('total_cancellations', 'N/A')}")
    print(f"  Mean / route       : {stats.get('mean', 0):.1f}")
    print(f"  Median / route     : {stats.get('median', 0):.1f}")
    print(f"  Std dev            : {stats.get('std', 0):.1f}")
    print(f"  IQR                : {stats.get('iqr', 0):.1f}")
    print()
    print("--- Weekday vs Weekend ---")
    print(
        f"  Weekday            : {wkd.get('weekday_cancellations', 'N/A')} "
        f"({wkd.get('weekday_proportion', 0):.1%})"
    )
    print(
        f"  Weekend            : {wkd.get('weekend_cancellations', 'N/A')} "
        f"({wkd.get('weekend_proportion', 0):.1%})"
    )
    print()
    print("--- Trend Over Time ---")
    print(f"  Direction          : {trends.get('trend', 'N/A')}")
    print(f"  Weekly slope       : {trends.get('slope', 0):.2f} trips/week")
    print()
    print("--- Anomalies ---")
    print(f"  Anomalous routes   : {anomalies.get('anomaly_count', 'N/A')}")
    print(
        f"  Z-score threshold  : {anomalies.get('z_score_threshold', Z_SCORE_OUTLIER_THRESHOLD)}"
    )
    print("=" * 60)


# ---------------------------------------------------------------------------
# 20. main
# ---------------------------------------------------------------------------
def main():
    """Entry point: load data, preprocess, run all analyses, print summary.

    Returns
    -------
    dict  – full analysis results (useful when called from notebooks/tests).
    """
    details, by_day, by_route = load_cancellation_data()
    details = preprocess_data(details)
    results = run_all_analyses(details, by_day, by_route)
    print_summary(results)
    return results


if __name__ == "__main__":
    main()
