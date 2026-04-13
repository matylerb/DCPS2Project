"""
Visualisation - Dublin Bus Cancellations
Author: Illya Mikava - Data Visualisation

Charts produced:
1. Bar chart   - cancellations by day of week
2. Line chart  - cancellations over time
3. Heatmap     - top 20 routes by day of week
4. Horiz. bar  - top 20 worst routes overall
5. Bar chart   - strike vs non-strike days
6. Line chart  - cumulative cancellations over time
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt, matplotlib.dates as mdates, matplotlib.cm as cm
import seaborn as sns

# Apply seaborn theme globally for consistent, professional look
sns.set_theme(style="whitegrid")

# Global font and style settings
plt.rcParams["font.size"] = 11
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["figure.dpi"] = 150

# Constants for file paths
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE, '..', 'data', 'processed')
OUTPUT_DIR = os.path.join(BASE, '..', 'outputs', 'figures')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Constants for colours and day ordering
RED  = "#C62828"
BLUE = "#1565C0"
GREY = "#B0BEC5"
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def save(filename):
    """Save the current figure and close it."""
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=150)
    plt.close()
    print(f"Saved: {filename}")


def load_data():
    """Load the three processed CSVs produced by data_engineering.py."""
    by_day   = pd.read_csv(os.path.join(DATA_DIR, "cancellations_by_day.csv"))
    by_route = pd.read_csv(os.path.join(DATA_DIR, "cancellations_by_route.csv"))
    details  = pd.read_csv(os.path.join(DATA_DIR, "all_cancellation_details.csv"),
                           parse_dates=["date"])
    return by_day, by_route, details


# Chart 1: Bar chart - cancellations by day of week
def plot_by_day(by_day):
    by_day["day"] = pd.Categorical(by_day["day"], categories=DAY_ORDER, ordered=True)
    by_day = by_day.sort_values("day")

    # Monday and Tuesday are red (strike days), others blue, zeros grey
    colors = []
    for _, row in by_day.iterrows():
        if row["day"] in ("Monday", "Tuesday"):
            colors.append(RED)
        elif row["cancelled_trips"] > 0:
            colors.append(BLUE)
        else:
            colors.append(GREY)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(by_day["day"], by_day["cancelled_trips"], color=colors, width=0.6)
    ax.bar_label(bars, fmt=lambda v: f"{v:,.0f}" if v > 0 else "No data",
                 padding=5, fontsize=10, fontweight="bold")

    ax.set_title("Dublin Bus Cancellations by Day of Week\nRed = strike days (Mon & Tue)  |  Grey = no data recorded (Sat & Sun)")
    ax.set_ylabel("Cancelled Trips")
    ax.set_ylim(0, by_day["cancelled_trips"].max() * 1.18)
    save("01_cancellations_by_day.png")


# Chart 2: Line chart - cancellations over time
def plot_timeline(details):
    by_date = details.groupby("date")["trip_id"].nunique().reset_index()
    by_date.columns = ["date", "cancelled_trips"]
    by_date = by_date.sort_values("date")

    fig, ax = plt.subplots(figsize=(14, 5))

    # Use markers so only real data points are visible (no implied continuity)
    ax.plot(by_date["date"], by_date["cancelled_trips"],
            color=BLUE, linewidth=2, marker="o", markersize=5)
    ax.fill_between(by_date["date"], by_date["cancelled_trips"], alpha=0.15, color=BLUE)

    # Highlight big spike dates (strikes)
    spikes = by_date[by_date["cancelled_trips"] > 5000]
    ax.scatter(spikes["date"], spikes["cancelled_trips"], color=RED, s=80, zorder=5)
    for _, row in spikes.iterrows():
        ax.annotate(f"{int(row['cancelled_trips']):,}",
                    xy=(row["date"], row["cancelled_trips"]),
                    xytext=(0, 10), textcoords="offset points",
                    ha="center", fontsize=8, color=RED, fontweight="bold")

    # Clip x-axis to actual data range so empty future space is removed
    ax.set_xlim(by_date["date"].min(), by_date["date"].max())

    ax.set_title("Dublin Bus Cancellations Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cancelled Trips")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    plt.xticks(rotation=30, ha="right")
    save("02_cancellations_timeline.png")


# Chart 3: Heatmap - top 20 routes and day of week
def plot_heatmap(details):
    top20_routes = (details.groupby("route_short_name")["trip_id"]
                    .nunique()
                    .nlargest(20)
                    .index)

    pivot = (details[details["route_short_name"].isin(top20_routes)]
             .groupby(["route_short_name", "day_of_week"])["trip_id"]
             .nunique()
             .unstack(fill_value=0))

    pivot = pivot[[d for d in DAY_ORDER if d in pivot.columns]]
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    # Clean up trailing dash artefacts on route labels
    pivot.index = pivot.index.str.strip(" -")

    fig, ax = plt.subplots(figsize=(11, 8))
    sns.heatmap(pivot, ax=ax, cmap="YlOrRd", annot=True, fmt="d",
                linewidths=0.4, cbar_kws={"label": "Cancelled Trips"})

    ax.set_title("Top 20 Routes - Cancellations by Day of Week\nNote: Sat & Sun not shown - dataset covers weekday services only")
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Route")
    plt.xticks(rotation=30)
    plt.yticks(rotation=0)
    save("03_heatmap_route_x_day.png")


# Chart 4: Horizontal bar - top 20 worst routes
def plot_top_routes(by_route):
    top20 = by_route.head(20).sort_values("total_cancelled_trips", ascending=True).copy()

    colors = cm.RdYlGn(np.linspace(0, 1, len(top20)))

    fig, ax = plt.subplots(figsize=(11, 9))
    bars = ax.barh(top20["route_short_name"], top20["total_cancelled_trips"],
                   color=colors, height=0.7)
    ax.bar_label(bars, labels=[f"{int(v):,}" for v in top20["total_cancelled_trips"]],
                 padding=4, fontsize=9)

    ax.set_title("Top 20 Most Cancelled Dublin Bus Routes")
    ax.set_xlabel("Total Cancelled Trips")
    ax.set_ylabel("Route")
    ax.set_xlim(0, top20["total_cancelled_trips"].max() * 1.12)
    save("04_top20_routes.png")


# Chart 5: Strike vs Non-Strike day comparison (NEW)
def plot_strike_vs_nonstrike(details):
    details = details.copy()
    details["is_strike"] = details["day_of_week"].isin(["Monday", "Tuesday"])

    strike_total     = details[details["is_strike"]]["trip_id"].nunique()
    non_strike_total = details[~details["is_strike"]]["trip_id"].nunique()

    labels = ["Strike Days\n(Mon & Tue)", "Non-Strike Days\n(Wed-Fri)"]
    values = [strike_total, non_strike_total]
    colors = [RED, BLUE]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=colors, width=0.5)
    ax.bar_label(bars, fmt=lambda v: f"{v:,.0f}", padding=6, fontsize=11, fontweight="bold")

    ax.set_title("Strike vs Non-Strike Day Cancellations\nTotal unique cancelled trips across all dates in each category")
    ax.set_ylabel("Total Cancelled Trips")
    ax.set_ylim(0, max(values) * 1.18)
    save("05_strike_vs_nonstrike.png")


# Chart 6: Cumulative cancellations over time (NEW)
def plot_cumulative(details):
    by_date = details.groupby("date")["trip_id"].nunique().reset_index()
    by_date.columns = ["date", "cancelled_trips"]
    by_date = by_date.sort_values("date")

    # Running total using np.cumsum
    by_date["cumulative"] = np.cumsum(by_date["cancelled_trips"].values)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(by_date["date"], by_date["cumulative"],
            color=BLUE, linewidth=2, marker="o", markersize=4)
    ax.fill_between(by_date["date"], by_date["cumulative"], alpha=0.12, color=BLUE)

    # Clip x-axis to real data range
    ax.set_xlim(by_date["date"].min(), by_date["date"].max())

    ax.set_title("Cumulative Dublin Bus Cancellations Over Time\nRunning total - shows the full scale of the problem building up over the period")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Cancelled Trips")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    plt.xticks(rotation=30, ha="right")
    save("06_cumulative_cancellations.png")


# Main
if __name__ == "__main__":
    print("Loading data...")
    by_day, by_route, details = load_data()

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

    print("\nDone! All charts saved to outputs/figures/")