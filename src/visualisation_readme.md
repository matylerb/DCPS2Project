# visualisation_readme.md — `visualisation.py`

## Overview
`visualisation.py` reads the three processed CSV files from `data_engineering.py` and produces 6 charts saved as PNG images in `outputs/figures/`.

**Author:** Illya Mikava

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pandas` | Loads and reshapes the CSV data |
| `matplotlib` | Draws all charts |
| `seaborn` | Global theme and heatmap (Chart 3) |
| `numpy` | Colourmap gradient (Chart 4) and cumulative total (Chart 6) |

---

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `RED` | `#C62828` | Colour used for strike days and spike markers |
| `BLUE` | `#1565C0` | Colour used for normal cancellation bars and lines |
| `GREY` | `#B0BEC5` | Colour used for days with no data (Sat & Sun) |
| `DAY_ORDER` | Mon–Sun | Keeps day columns in the correct order across all charts |

---

## Functions

### `save(filename)`
Helper used at the end of every chart function. Tidies the layout, saves the chart as a PNG to `outputs/figures/`, and closes the figure.

---

### `load_data()`
Reads the three processed CSVs and returns them as DataFrames.
- `cancellations_by_day.csv` — totals per day of week
- `cancellations_by_route.csv` — totals per route
- `all_cancellation_details.csv` — every individual cancellation with date and route info

---

### `plot_by_day(by_day)` → Chart 1
Bar chart of cancellations by day of week. Monday and Tuesday bars are red (strike days), other weekdays are blue, and Saturday/Sunday are grey with a "No data" label since the dataset only covers weekday services.

---

### `plot_timeline(details)` → Chart 2
Line chart showing cancellations day by day across the full date range. Uses markers on actual data points only to avoid implying continuity. The x-axis is clipped to the real data range. Days with more than 5,000 cancellations get a red dot and a count label — these are the strike days.

---

### `plot_heatmap(details)` → Chart 3
Grid showing the top 20 worst routes against each day of the week. Cells are coloured yellow (low) to red (high), with the exact count shown inside each cell. The worst route overall is at the top. Saturday and Sunday are not shown as no weekend data exists in the dataset.

---

### `plot_top_routes(by_route)` → Chart 4
Horizontal bar chart of the 20 routes with the most cancellations. Bars are coloured on a green-to-red gradient using `cm.RdYlGn` — green for the least cancelled routes at the bottom, red for the worst at the top.

---

### `plot_strike_vs_nonstrike(details)` → Chart 5
Side-by-side bar chart comparing total cancellations on strike days (Monday & Tuesday) versus non-strike weekdays (Wednesday–Friday). Red bar for strike days, blue for non-strike. Shows the direct impact of the strikes in a single clear visual.

---

### `plot_cumulative(details)` → Chart 6
Line chart showing the running total of cancellations across the full study period, calculated using `np.cumsum`. Shows the full scale of the problem building up over time, and is a natural companion to Chart 2.

---

## Output Files

| File | Chart |
|------|-------|
| `01_cancellations_by_day.png` | Bar chart by day of week |
| `02_cancellations_timeline.png` | Line chart over time |
| `03_heatmap_route_x_day.png` | Heatmap — routes vs days |
| `04_top20_routes.png` | Horizontal bar — top 20 routes |
| `05_strike_vs_nonstrike.png` | Strike vs non-strike day comparison |
| `06_cumulative_cancellations.png` | Cumulative cancellations over time |

---

## How to Run
```bash
python src/visualisation.py
```