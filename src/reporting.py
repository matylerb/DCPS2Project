"""
Reporting - Dublin Bus Cancellation Analysis
Author: Ivan Kubskyi - Reporting

Reads processed CSV outputs from data_engineering.py and generates
a structured markdown report saved to outputs/reports/report.md
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
DATA_DIR = BASE / "data" / "processed"
REPORTS_DIR = BASE / "outputs" / "reports"
FIGURES_DIR = BASE / "outputs" / "figures"

os.makedirs(REPORTS_DIR, exist_ok=True)


def load_data():
    """Load the three processed CSVs produced by data_engineering.py."""
    by_day = pd.read_csv(DATA_DIR / "cancellations_by_day.csv")
    by_route = pd.read_csv(DATA_DIR / "cancellations_by_route.csv")
    details = pd.read_csv(DATA_DIR / "all_cancellation_details.csv", parse_dates=["date"])
    return by_day, by_route, details


def summary_stats(by_day, by_route, details):
    """Compute top-level summary numbers for the report."""
    total_cancellations = int(details["trip_id"].nunique())
    total_routes = int(by_route["route_short_name"].nunique())
    total_dates = int(details["date"].nunique())

    top_route = by_route.iloc[0]
    top_day = by_day.loc[by_day["cancelled_trips"].idxmax()]
    weekend_total = int(by_day[by_day["day"].isin(["Saturday", "Sunday"])]["cancelled_trips"].sum())

    weekday_total = int(by_day[~by_day["day"].isin(["Saturday", "Sunday"])]["cancelled_trips"].sum())

    # Average cancellations per affected date
    avg_per_day = round(total_cancellations / total_dates, 1) if total_dates > 0 else 0

    return {
        "total_cancellations": total_cancellations,
        "total_routes": total_routes,
        "total_dates": total_dates,
        "avg_per_day": avg_per_day,
        "top_route_name": top_route["route_short_name"],
        "top_route_desc": top_route["route_long_name"],
        "top_route_count": int(top_route["total_cancelled_trips"]),
        "top_day_name": top_day["day"],
        "top_day_count": int(top_day["cancelled_trips"]),
        "weekend_total": weekend_total,
        "weekday_total": weekday_total,
    }


def format_route_table(by_route, n=10):
    """Return markdown table of top N cancelled routes."""
    top = by_route.head(n).copy()
    lines = []
    lines.append("| Rank | Route | Description | Cancelled Trips | Affected Dates |")
    lines.append("|------|-------|-------------|----------------|----------------|")
    for i, row in top.iterrows():
        rank = i + 1
        lines.append(
            f"| {rank} | **{row['route_short_name']}** | {row['route_long_name']} "
            f"| {int(row['total_cancelled_trips']):,} | {int(row['cancelled_dates'])} |"
        )
    return "\n".join(lines)


def format_day_table(by_day):
    """Return markdown table of cancellations by day of week."""
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day["day"] = pd.Categorical(by_day["day"], categories=day_order, ordered=True)
    by_day = by_day.sort_values("day")

    total = by_day["cancelled_trips"].sum()
    lines = []
    lines.append("| Day | Cancelled Trips | % of Total |")
    lines.append("|-----|----------------|------------|")
    for _, row in by_day.iterrows():
        pct = f"{row['cancelled_trips'] / total * 100:.1f}%" if total > 0 else "0%"
        note = " *(strike days)*" if row["day"] in ["Monday", "Tuesday"] else ""
        lines.append(f"| {row['day']}{note} | {int(row['cancelled_trips']):,} | {pct} |")
    return "\n".join(lines)


def agency_breakdown(details):
    """Return markdown table of cancellations by agency."""
    agency_map = {
        "7778019": "Bus Átha Cliath (Dublin Bus)",
        "7778002": "Nitelink",
        "7778021": "Go-Ahead Ireland",
    }
    grouped = details.groupby("agency_id")["trip_id"].nunique().reset_index()
    grouped.columns = ["agency_id", "cancelled_trips"]
    grouped["agency_id"] = grouped["agency_id"].astype(str)
    grouped["agency_name"] = grouped["agency_id"].map(agency_map).fillna(grouped["agency_id"])
    grouped = grouped.sort_values("cancelled_trips", ascending=False)

    total = grouped["cancelled_trips"].sum()
    lines = []
    lines.append("| Agency | Cancelled Trips | % of Total |")
    lines.append("|--------|----------------|------------|")
    for _, row in grouped.iterrows():
        pct = f"{row['cancelled_trips'] / total * 100:.1f}%" if total > 0 else "0%"
        lines.append(f"| {row['agency_name']} | {int(row['cancelled_trips']):,} | {pct} |")
    return "\n".join(lines)


def date_range_info(details):
    """Return string with date range covered by the dataset."""
    min_date = details["date"].min().strftime("%d %B %Y")
    max_date = details["date"].max().strftime("%d %B %Y")
    return f"{min_date} – {max_date}"


def generate_report(by_day, by_route, details):
    """Build the full markdown report string."""
    stats = summary_stats(by_day, by_route, details)
    route_table = format_route_table(by_route, n=10)
    day_table = format_day_table(by_day)
    agency_table = agency_breakdown(details)
    date_range = date_range_info(details)
    generated_on = datetime.now().strftime("%d %B %Y")

    report = f"""# Dublin Bus Cancellation Analysis — Report

**Module:** DATA 2005 Data Centric Programming  
**Team:** Cillian Chatham, Tyler Brady, Ilya Mikava, Ivan Kubskyi  
**Report author:** Ivan Kubskyi (Reporting)  
**Generated:** {generated_on}  
**Data coverage:** {date_range}

---

## 1. Introduction

Dublin Bus is the main public transport operator in the Greater Dublin Area, running hundreds of routes across the city and suburbs. This report summarises the findings of a data engineering and analysis pipeline applied to GTFS (General Transit Feed Specification) static data published by Ireland's National Transport Authority (NTA).

The central question this project investigates is: **which routes, days, and time periods are most affected by service cancellations** — or "ghost buses" — trips that are scheduled but never actually run.

The pipeline was built in Python and covers data loading, cleaning, validation, cancellation analysis, web scraping, and export. This report draws on the processed output files to present the findings clearly.

---

## 2. Dataset Overview

The analysis uses seven GTFS files from Transport for Ireland covering Dublin Bus, Nitelink, and Go-Ahead Ireland services.

| File | Records | Description |
|------|---------|-------------|
| stop_times_dublin_bus.txt | 4,349,048 | Scheduled arrival/departure times at every stop |
| trips.txt | 249,682 | Individual bus journeys |
| routes.txt | 805 (172 Dublin Bus) | Route definitions |
| calendar.txt | 314 | Weekly service schedules |
| calendar_dates.txt | 2,444 | Service exceptions — cancellations (type 2) and additions (type 1) |
| stops.txt | 14,024 | Stop names and GPS coordinates |
| agency.txt | 101 | Transit operators |

**Data period covered:** {date_range}

---

## 3. High-Level Summary

| Metric | Value |
|--------|-------|
| Total unique cancelled trips | {stats["total_cancellations"]:,} |
| Dublin Bus routes affected | {stats["total_routes"]} |
| Unique dates with cancellations | {stats["total_dates"]} |
| Average cancellations per affected date | {stats["avg_per_day"]:,} |
| Most cancelled route | {stats["top_route_name"]} — {stats["top_route_desc"]} ({stats["top_route_count"]:,} trips) |
| Day with most cancellations | {stats["top_day_name"]} ({stats["top_day_count"]:,} trips) |
| Weekend cancellations | {stats["weekend_total"]:,} |
| Weekday cancellations | {stats["weekday_total"]:,} |

The most striking finding is that **all cancellations fall on weekdays** — zero cancellations were recorded on Saturdays or Sundays. This strongly suggests the disruption is tied to weekday operational pressures, not random or weather-related factors.

---

## 4. Cancellations by Day of Week

{day_table}

Monday and Tuesday account for the largest share of cancellations, which the visualisation team identified as corresponding to **strike days**. Wednesday through Friday show a consistent lower level, and weekends are completely unaffected.

![Cancellations by Day of Week](../../outputs/figures/01_cancellations_by_day.png)

---

## 5. Most Cancelled Routes

The table below shows the ten routes with the highest number of cancelled trips across the analysis period.

{route_table}

Route **S4** (Liffey Valley – UCD) is the worst affected with {stats["top_route_count"]:,} cancelled trips. This route serves a high-demand corridor connecting a major shopping and employment hub to University College Dublin, so repeated cancellations will have a significant impact on both students and commuters.

Routes in the **N** series (night services), **S** series (orbital routes), and **W** series (west Dublin orbital) appear heavily in the top rankings, suggesting these newer or less-resourced service families may be more vulnerable to cancellations.

![Top 20 Most Cancelled Routes](../../outputs/figures/04_top20_routes.png)

---

## 6. Strike vs Non-Strike Days

A key finding from the visualisation work is that the cancellation pattern clusters strongly around known strike days. The chart below breaks cancellations into strike days (Monday and Tuesday) versus non-strike weekdays (Wednesday–Friday).

![Strike vs Non-Strike](../../outputs/figures/05_strike_vs_nonstrike.png)

This distinction is important: it means that while {stats["total_cancellations"]:,} trips were cancelled in total, a significant proportion are attributable to a small number of industrial action days rather than chronic everyday unreliability.

---

## 7. Cancellations Over Time

The timeline and cumulative charts show how cancellations are distributed across the data period.

![Cancellations Over Time](../../outputs/figures/02_cancellations_timeline.png)

![Cumulative Cancellations](../../outputs/figures/06_cumulative_cancellations.png)

The cumulative chart illustrates the total scale of disruption building up over the period — useful for understanding the long-run impact on regular commuters.

---

## 8. Agency Breakdown

The three Dublin Bus operators contribute differently to the cancellation total:

{agency_table}

---

## 9. Route Heatmap

The heatmap below shows cancellations for the top 20 routes broken down by day of week, making the strike-day pattern immediately visible.

![Route × Day Heatmap](../../outputs/figures/03_heatmap_route_x_day.png)

---

## 10. Conclusion

The analysis shows that Dublin Bus service cancellations are concentrated in specific, identifiable patterns:

- **All cancellations are weekday-only** — weekends are completely unaffected in this dataset.
- **Strike days (Monday and Tuesday) drive the majority of cancellations**, particularly the peak on Tuesday with {stats["top_day_count"]:,} affected trips.
- **Route S4** is the single most affected route, followed by N6, 73, S6, and W2.
- **Newer orbital and suburban route families** (S, N, W, L series) appear disproportionately affected compared to legacy core routes.

For commuters, the practical takeaway is clear: the highest risk of encountering a ghost bus is on a Monday or Tuesday, on suburban orbital routes. For the NTA and Dublin Bus management, the concentration of cancellations on strike days suggests that contingency planning for industrial action is the key lever for reducing the cancellation rate.

---

## 11. References

- Transport for Ireland / National Transport Authority — GTFS Static Data: https://www.transportforireland.ie/
- Google Developers — GTFS Static Reference: https://developers.google.com/transit/gtfs/reference
- Dublin Live — Dublin Bus cancellation news coverage (scraped via Google News RSS)
- Met Éireann — Historical weather observations: https://www.met.ie/
"""
    return report


def save_report(content):
    """Save the report markdown to outputs/reports/report.md."""
    output_path = REPORTS_DIR / "report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Report saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    print("Loading processed data...")
    by_day, by_route, details = load_data()

    print("Generating report...")
    report_content = generate_report(by_day, by_route, details)

    path = save_report(report_content)
    print(f"Done. Report written to {path}")
