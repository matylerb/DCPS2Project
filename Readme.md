# Dublin Bus Cancellation Analysis - Data Engineering

**Course:** Data Centric Programming
**Domain:** Transportation & Mobility
**Thesis:** Frquent cancellation and scheduling of Dublin Busses that never show up ("ghost busses)


## Team Members

| Name | Role |
|------|------|
| Cillian Chatham | Data Engineer |
| Tyler Brady | Analyst |
| Ilya Mikava | Visualization Lead |
| Ivan Kubskyi | Reporting |

## Project Overview

This project analyses GTFS (General Transit Feed Specification) data from Ireland's National Transport Authority (NTA) to investigate the frequency and patterns of Dublin Bus service cancellations. We examine which routes, days, and times are most affected by cancelled services & buses that are scheduled to run but never actually show up.

## Key findings

- **Route S4 (Liffey Valley – UCD)** has the most cancellations with 856 cancelled trips
- **Tuesdays** have the highest cancellation count (10,456 affected trips)
- **Zero weekend cancellations** — all cancellations affect weekday commuters
- **172 Dublin Bus routes** analysed across 86,535 trips
- **2,444 service exception records** found in the GTFS data, of which 1,383 are service removals (cancellations)
- Popular commuter routes like **39A, 15, 73, N6** are among the worst affected


## Data Source

- **GTFS Static Data** from [Transport for Ireland / National Transport Authority](https://www.transportforireland.ie/)
- **Web-scraped data** from Dublin Live and Met Éireann (for supplementary evidence)

### GTFS Files Used

| File | Records | Description |
|------|---------|-------------|
| stop_times_dublin_bus.txt | 4,349,048 | Scheduled arrival/departure at every stop |
| trips.txt | 249,682 | Individual bus journeys |
| routes.txt | 805 (172 Dublin) | Route definitions |
| calendar.txt | 314 | Service schedules (days of week, date ranges) |
| calendar_dates.txt | 2,444 | Service exceptions — cancellations (type 2) and additions (type 1) |
| stops.txt | 14,024 | Stop names and GPS coordinates |
| agency.txt | 101 | Transit operators |


### Dublin Bus agency IDs

- `7778019` — Bus Átha Cliath (Dublin Bus)
- `7778002` — Nitelink (Dublin Bus night services)
- `7778021` — Go-Ahead Ireland (Dublin area routes)

## Project Structure

```
DCPS2Project/
├── data/
│   ├── raw/                          # Original GTFS files
│   └── processed/                    # Exported analysis results
├── src/
│   ├── data_engineering.py           # Data loading, cleaning, analysis, export
│   ├── ananlysis.py                  # Statistical analysis
│   └── visualisation.py              # Data visualisation
├── outputs/
│   ├── figures/                      # Charts and plots
│   └── reports/                      # Written reports
├── notebooks/                      
├── requirements.txt
└── README.md
```

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/matylerb/DCPS2Project.git
cd DCPS2Project/DCPS2Project
```

### 2. Install dependancies
```bash
pip install -r requirements.txt
```

### 3. Add data files

Place all GTFS .txt files in data/raw/. The stop_times_dublin_bus.txt file is a pre-filtered version containing only Dublin Bus stop times (~200MB, 4.35M rows).

### 4. Run the data engineering pipeline
```bash
cd src
python data_engineering.py
```

This runs the full pipeline: Load -> Clean -> Validate -> Analyse -> Scrape -> Export

## Data Engineering Pipeline

The pipeline (data_engineering.py) is organised into 5 sections:

### Section 1: Data Loading
- Loads all 7 GTFS files with proper dtype handling
- Parses dates from YYYYMMDD format to datetime objects
- Handles UTF-8 BOM encoding and Windows line endings

### Section 2: Data Cleaning & Validation
- Filters to Dublin Bus routes (agencies 7778019, 7778002, 7778021)
- Parses GTFS times to seconds using NumPy vectorised operations
- Handles overnight services (times > 24:00:00)
- Validates referential integrity across all tables

### Section 3: Cancellation Analysis
- Identifies cancelled services from calendar_dates.txt (exception_type = 2)
- Maps cancellations to specific routes via trips
- Ranks routes by cancellation frequency
- Analyses patterns by day of week and month

### Section 4: Web Scraping
- Scrapes Dublin Live for news about bus cancellations (BeautifulSoup)
- Scrapes Met Éireann for weather data to correlate with cancellations
- Includes rate limiting and error handling

### Section 5: Data Export
- Exports all results in both CSV and JSON formats
- Outputs saved to data/processed/ for use by Analyst and Visualization Leads

## Technical Highlights

- NumPy vectorisation for time parsing across 4.35M rows (no loops)
- Pandas for data loading, merging, and aggregation
- BeautifulSoup for web scraping supplementary data
- Modular design with documented functions and docstrings
- Logging throughout (not print statements)
- Error handling on all file operations and web requests
- Dual export — all results in both CSV and JSON formats
- PEP 8 compliant code style

## Libraries Used

- numpy — Vectorised numerical operations
- pandas — Data manipulation and analysis
- matplotlib — Static visualizations
- seaborn — Statistical visualizations
- requests — HTTP requests for web scraping
- beautifulsoup4 — HTML parsing
- json / csv — Data serialization

## License

This project is for an academic purpose as part of the DATA 2005 DataCentricProgramming module in TUDublin

