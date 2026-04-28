import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
from pathlib import Path
from ananlysis import main as run_analysis
from visualisation import (
    load_data as load_vis_data,
    plot_by_day,
    plot_timeline,
    plot_heatmap,
    plot_top_routes,
    plot_strike_vs_nonstrike,
    plot_cumulative,
)
from reporting import load_data as load_report_data, generate_report, save_report


def run_data_engineering():
    print("\n=== Data Engineering ===")
    print("Raw GTFS data not available locally — loading from processed outputs.")

    processed_dir = Path(__file__).parent / "data" / "processed"
    route_rankings = pd.read_csv(processed_dir / "cancellations_by_route.csv")
    day_patterns = pd.read_csv(processed_dir / "cancellations_by_day.csv")

    print(f"Loaded {len(route_rankings)} routes and {len(day_patterns)} day records from processed data.")

    print("\nTop 10 Most Cancelled Routes:")
    print("=" * 60)
    print(route_rankings.head(10).to_string(index=False))

    print("\nCancellations by Day of Week:")
    print("-" * 40)
    print(day_patterns.to_string(index=False))


def run_visualisation():
    print("\n=== Visualisation ===")
    by_day, by_route, details = load_vis_data()

    print("Chart 1 - cancellations by day of week")
    plot_by_day(by_day)

    print("Chart 2 - cancellations over time")
    plot_timeline(details)

    print("Chart 3 - heatmap (routes x days)")
    plot_heatmap(details)

    print("Chart 4 - top 20 routes")
    plot_top_routes(by_route)

    print("Chart 5 - strike vs non-strike days")
    plot_strike_vs_nonstrike(details)

    print("Chart 6 - cumulative cancellations")
    plot_cumulative(details)


def run_reporting():
    print("\n=== Reporting ===")
    by_day, by_route, details = load_report_data()
    report_content = generate_report(by_day, by_route, details)
    path = save_report(report_content)
    print(f"Report saved to: {path}")


def main():
    run_data_engineering()

    print("\n=== Analysis ===")
    run_analysis()

    run_visualisation()
    run_reporting()

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()

