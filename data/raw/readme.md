# Raw Data

This folder contains the original GTFS (General Transit Feed Specification) data from the National Transport Authority (NTA).

## Source

Downloaded from [Transport for Ireland](https://www.transportforireland.ie/transitData/Data/GTFS_Realtime.zip)

## Files

- `agency.txt` — Transit operator information (101 operators)
- `calendar.txt` — Service schedules: which days each service runs (314 services)
- `calendar_dates.txt` — Service exceptions: added (type 1) or cancelled (type 2) dates (2,444 records)
- `feed_info.txt` — Feed metadata (valid March 2026 – March 2027)
- `routes.txt` — Route definitions (805 routes, 172 Dublin Bus)
- `shapes.txt` — GPS coordinates for route paths on a map
- `stop_times.txt` — Full stop times for all operators (~400MB)
- `stop_times_dublin_bus.txt` — Pre-filtered stop times for Dublin Bus only (4,349,048 rows)
- `stops.txt` — Stop names and GPS coordinates (14,024 stops)
- `translations.txt` — Translated text for stop names
- `trips.txt` — Individual bus journeys (249,682 trips)

## Notes

- These files are not tracked in git due to their size
- To regenerate `stop_times_dublin_bus.txt`, run the `filter_stop_times.py` script against the full `stop_times.txt`