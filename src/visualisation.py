"""
Visualisation - Dublin Bus Cancellations
Author: Illya Mikava - Data Visualisation

Charts produced:
1. Bar chart   - cancellations by day of week
2. Line chart  - cancellations over time
3. Heatmap     - top 20 routes by day of week
4. Horiz. bar  - top 20 worst routes overall
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# Constants for file paths and styling
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE, '..', 'data', 'processed')
OUTPUT_DIR = os.path.join(BASE, '..', 'outputs', 'figures')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Constants for colours and ordering 
RED  = "#C62828"   # strike / high-cancellation colour
BLUE = "#1565C0"   # normal cancellation colour
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]


# Where to save Charts
def save(filename):
    """Tighten layout, save to OUTPUT_DIR and close the figure."""
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=150)
    plt.close()
    print(f"Saved: {filename}")

# Data loading
def load_data():
    """Load the three processed CSVs produced by data_engineering.py."""
    by_day   = pd.read_csv(os.path.join(DATA_DIR, "cancellations_by_day.csv"))
    by_route = pd.read_csv(os.path.join(DATA_DIR, "cancellations_by_route.csv"))
    details  = pd.read_csv(os.path.join(DATA_DIR, "all_cancellation_details.csv"),
                           parse_dates=["date"])
    return by_day, by_route, details


# Chart 1: Bar chart – cancellations by day of week
def plot_by_day(by_day):
    by_day["day"] = pd.Categorical(by_day["day"], categories=DAY_ORDER, ordered=True)
    by_day = by_day.sort_values("day")

    # Colour strike days (Mon/Tue) red, rest blue (or grey if zero)
    colors = []
    for _, row in by_day.iterrows():
        if row["day"] in ("Monday", "Tuesday"):
            colors.append(RED)
        elif row["cancelled_trips"] > 0:
            colors.append(BLUE)
        else:
            colors.append("#ECEFF1")

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(by_day["day"], by_day["cancelled_trips"], color=colors, width=0.6)

    # Value labels above each collumn
    ax.bar_label(bars, fmt=lambda v: f"{v:,.0f}", padding=5, fontsize=10, fontweight="bold")

    ax.set_title("Dublin Bus Cancellations by Day of Week", fontsize=14, fontweight="bold")
    ax.set_ylabel("Cancelled Trips")
    ax.set_ylim(0, by_day["cancelled_trips"].max() * 1.15)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    save("01_cancellations_by_day.png")


# Chart 2: Line chart – cancellations over time
def plot_timeline(details):
    by_date = (details.groupby(["date", "day_of_week"])["trip_id"]
               .nunique()
               .reset_index(names=["date", "day_of_week", "cancelled_trips"])
               if False  # placeholder – real groupby below
               else details.groupby("date")["trip_id"].nunique().reset_index())
    by_date.columns = ["date", "cancelled_trips"]
    by_date = by_date.sort_values("date")

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(by_date["date"], by_date["cancelled_trips"], color=BLUE, linewidth=2)
    ax.fill_between(by_date["date"], by_date["cancelled_trips"], alpha=0.15, color=BLUE)

    # Highlight big spike dates (strikes)
    spikes = by_date[by_date["cancelled_trips"] > 5000]
    ax.scatter(spikes["date"], spikes["cancelled_trips"], color=RED, s=80, zorder=5)
    for _, row in spikes.iterrows():
        ax.annotate(f"{int(row['cancelled_trips']):,}",
                    xy=(row["date"], row["cancelled_trips"]),
                    xytext=(0, 10), textcoords="offset points",
                    ha="center", fontsize=8, color=RED, fontweight="bold")

    ax.set_title("Dublin Bus Cancellations Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cancelled Trips")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.xticks(rotation=30)
    save("02_cancellations_timeline.png")


# Chart 3: Heatmap – top 20 routes and day of week
def plot_heatmap(details):
    top20_routes = (details.groupby("route_short_name")["trip_id"]
                    .nunique()
                    .nlargest(20)
                    .index)

    pivot = (details[details["route_short_name"].isin(top20_routes)]
             .groupby(["route_short_name", "day_of_week"])["trip_id"]
             .nunique()
             .unstack(fill_value=0))

    # Keep only days present, in correct order; sort worst route to top
    pivot = pivot[[d for d in DAY_ORDER if d in pivot.columns]]
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(11, 8))
    sns.heatmap(pivot, ax=ax, cmap="YlOrRd", annot=True, fmt="d",
                linewidths=0.4, cbar_kws={"label": "Cancelled Trips"})

    ax.set_title("Top 20 Routes - Cancellations by Day of Week", fontsize=14, fontweight="bold")
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Route")
    plt.xticks(rotation=30)
    plt.yticks(rotation=0)
    save("03_heatmap_route_x_day.png")


# Chart 4: Horizontal bar – top 20 worst routes 
def plot_top_routes(by_route):
    top20 = by_route.head(20).sort_values("total_cancelled_trips", ascending=True)

    fig, ax = plt.subplots(figsize=(11, 9))
    bars = ax.barh(top20["route_short_name"], top20["total_cancelled_trips"],
                   color=BLUE, height=0.7)
    ax.bar_label(bars, labels=[f"{int(v):,}" for v in top20["total_cancelled_trips"]],
                 padding=4, fontsize=9)

    ax.set_title("Top 20 Most Cancelled Dublin Bus Routes", fontsize=14, fontweight="bold")
    ax.set_xlabel("Total Cancelled Trips")
    ax.set_ylabel("Route")
    ax.set_xlim(0, top20["total_cancelled_trips"].max() * 1.1)
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    save("04_top20_routes.png")


# Main 
if __name__ == "__main__":
    print("Loading data...")
    by_day, by_route, details = load_data()

    print("Chart 1 - cancellations by day of week")
    plot_by_day(by_day)

    print("Chart 2 - cancellations over time")
    plot_timeline(details)

    print("Chart 3 - heatmap (routes * days)")
    plot_heatmap(details)

    print("Chart 4 - top 20 routes")
    plot_top_routes(by_route)

    print("\nDone! All charts saved to outputs/figures/")