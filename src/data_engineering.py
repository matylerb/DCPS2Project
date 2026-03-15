"""
Data Engineering - Dublin bus data

Author: Cillian Chatham - Data Engineer 

Handles loading, cleaning, validation, cancellation analysis,
and export of GTFS data for Dublin bus vehicles
"""

import pandas as pd
import numpy as np
import json
import csv
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Dublin bus agency IDs from agency.txt
DUBLIN_AGENCIES = {'7778019', '7778002', '7778021'}

# Path to raw data
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')

# ============================================================
# SECTION 1: DATA LOADING
# ============================================================

def load_gtfs_file(filepath, dtype_overrides=None):
    """
    Load a GTFS .txt file (CSV format) into a pandas DataFrame

    Parameters:
    filepath : str
        path to the txt file
    dtype_overrides : dict, optional
        column dtype overrides to prevent auto casting IDs to integers

    returns:
    pd.DataFrame 
        loaded and cleaned data frame

    """
    try:
        df = pd.read_csv(filepath, dtype=dtype_overrides, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        str_cols = df.select_dtypes(include=['object']).columns
        for col in str_cols:
            df[col]= df[col].str.strip()
        logger.info(f"Loaded {os.path.basename(filepath)}: {len(df):,} rows, {len(df.columns)} columns")
        return df
    except FileNotFoundError:
        logger.error(f"FIle not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        raise

def load_all_data(data_dir=DATA_DIR):
    """
    Load a GTFS files and return as a dictionary of a DataFRames

    Returns:
    dict
        Dictionary with keys: agency, routes, trips, calendar,
        calendar_dates, stops, stop_times
    """
    logger.info("=" * 60)
    logger.info("LOADING ALL GTFS DATA")
    logger.info("=" * 60)

    data = {}

    # agency
    data['agency'] = load_gtfs_file(
        os.path.join(data_dir, 'agency.txt'),
        dtype_overrides={'agency_id': str}
    )

    # routes
    data['routes'] = load_gtfs_file(
        os.path.join(data_dir, 'routes.txt'),
        dtype_overrides={'agency_id': str, 'route_id': str}
    )

    # trips
    data['trips'] = load_gtfs_file(
        os.path.join(data_dir, 'trips.txt'),
        dtype_overrides={'route_id': str, 'service_id': str, 'trip_id': str}
    )

    # Calendar — with date parsing
    data['calendar'] = load_gtfs_file(
        os.path.join(data_dir, 'calendar.txt'),
        dtype_overrides={'service_id': str}
    )
    data['calendar']['start_date'] = pd.to_datetime(data['calendar']['start_date'], format='%Y%m%d')
    data['calendar']['end_date'] = pd.to_datetime(data['calendar']['end_date'], format='%Y%m%d')

    # Calendar Dates KEY FILE FOR CANCELLATIONS
    # exception_type 1 = service ADDED, 2 = service REMOVED (cancelled)
    data['calendar_dates'] = load_gtfs_file(
        os.path.join(data_dir, 'calendar_dates.txt'),
        dtype_overrides={'service_id': str, 'exception_type': int}
    )
    data['calendar_dates']['date'] = pd.to_datetime(data['calendar_dates']['date'], format='%Y%m%d')

    # Stops
    data['stops'] = load_gtfs_file(
        os.path.join(data_dir, 'stops.txt'),
        dtype_overrides={'stop_id': str, 'parent_station': str}
    )

    # Stop Times largest file (~4.35M rows)
    data['stop_times'] = load_gtfs_file(
        os.path.join(data_dir, 'stop_times_dublin_bus.txt'),
        dtype_overrides={'trip_id': str, 'stop_id': str, 'stop_sequence': int}
    )

    logger.info("=" * 60)
    logger.info("ALL DATA LOADED SUCCESSFULLY")
    for name, df in data.items():
        logger.info(f"  {name}: {len(df):,} rows")
    logger.info("=" * 60)

    return data

# ============================================================
# SECTION 2: DATA CLEANING & VALIDATION
# ============================================================

def filter_dublin_bus_routes(routes_df):
    """FIlter routes to only DUblin bus, NiteLink, and go ahead ireland"""
    dublin_routes = routes_df[routes_df['agency_id'].isin(DUBLIN_AGENCIES)].copy()
    logger.info(f"Filtered to {len(dublin_routes)} Dublin Bus Routes (from {len(routes_df)} total)")
    return dublin_routes

def filter_dublin_trips(trips_df, dublin_routes_df):
    """FIlter trips to only those on Dublin BUs routes"""
    dublin_route_ids = set(dublin_routes_df['route_id'])
    dublin_trips = trips_df[trips_df['route_id'].isin(dublin_route_ids)].copy()
    logger.info(f"Filtered to {len(dublin_trips):,} Dublin BUs trips (from {len(trips_df):,} total)")
    return dublin_trips

def parse_times_vectorised(time_series):
    """
    Parse GTFS time strings to seconds using NumPy vectorisation

    GTFS aloows times > 24:00:00 for overnight services
    (eg: 25:30:00 = 1:30 am the next day)

    parameters:
    time_series : pd.Series
        series of time strings in HH:MM:SS format

    Returns:
    np.ndarray
        Array of total seconds since midnight
    """

    split = time_series.str.split(':', expand=True)
    split = split.apply(pd.to_numeric, errors='coerce')
    values = split.values.astype(float)
    # NumPy broadcasting hours * 3600 + minutes * 60 +seconds
    seconds = values[:, 0] * 3600 + values[:, 1] * 60 + values[:, 2]
    return seconds

def clean_stop_times(stop_times_df):
    """
    Clean stop times data

    Parse arrival/departure times to seconds (vectorised with NumPy)
    Flag overnight trips (>= 24:00:00)
    Calculate dwell time at each stop
    Add hour-of-day column for analysis

    parameters:
    stop_times_df: pd.dataframe
        Raw stop_times data

    returns:
    pd.DataFrame
        cleaned stop_times with new columns:
        arrival_seconds, departure_seconds, is_overnight, dwell_seconds, hour
    """
    df = stop_times_df.copy()

    logger.info("Parsing arrival/departure times (vectorised)...")
    df['arrival_seconds'] = parse_times_vectorised(df['arrival_time'])
    df['departure_seconds'] = parse_times_vectorised(df['departure_time'])

    # Flag overnight trips (times >= 24 hours = 86400 seconds)
    df['is_overnight'] = df['arrival_seconds'] >= 86400

    # Dwell time at each stop
    df['dwell_seconds'] = df['departure_seconds'] - df['arrival_seconds']

    # Hour of day for analysis 
    df['hour'] = (df['arrival_seconds'] // 3600).astype(int) % 24

    # Log data quality
    missing = df['arrival_seconds'].isna().sum()
    overnight = df['is_overnight'].sum()
    if missing > 0:
        logger.warning(f"Missing times: {missing:,}")
    logger.info(f"Overnight trips (>24:00): {overnight:,}")
    logger.info(f"Cleaned stop_times: {len(df):,} rows")

    return df

def validate_data(data_dict):
    """
    Run data integrity checks across the dataset

    checks for orphan references, null values, and expired services

    parameters
    data_dict : dict
        Dictionary of DataFrame from load_all_data()

    returns:
    list of str
        List of issues found
    """

    issues = []
    logger.info("Running data validation checks...")

    # Orphan trips (referencing non-existent routes)
    trip_route_ids = set(data_dict['trips']['route_id'])
    route_ids = set(data_dict['routes']['route_id'])
    orphan_routes = trip_route_ids - route_ids
    if orphan_routes:
        issues.append(f"WARNING: {len(orphan_routes)} trips reference non-existent routes")

    # Orphan stop_times (referencing non-existent trips)
    stop_time_trip_ids = set(data_dict['stop_times']['trip_id'])
    trip_ids = set(data_dict['trips']['trip_id'])
    orphan_trips = stop_time_trip_ids - trip_ids
    if orphan_trips:
        issues.append(f"WARNING: {len(orphan_trips)} stop_times reference non-existent trips")

    # Orphan stop_times (referencing non-existent stops)
    stop_time_stop_ids = set(data_dict['stop_times']['stop_id'])
    stop_ids = set(data_dict['stops']['stop_id'])
    orphan_stops = stop_time_stop_ids - stop_ids
    if orphan_stops:
        issues.append(f"WARNING: {len(orphan_stops)} stop_times reference non-existent stops")

    # Null values in critical columns
    critical_checks = {
        'stop_times': ['trip_id', 'arrival_time', 'departure_time', 'stop_id'],
        'trips': ['trip_id', 'route_id', 'service_id'],
        'routes': ['route_id', 'agency_id'],
    }
    for table_name, columns in critical_checks.items():
        df = data_dict[table_name]
        for col in columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    issues.append(f"WARNING: {null_count:,} null values in {table_name}.{col}")

    # Log results
    for issue in issues:
        logger.warning(issue)
    if not any(i.startswith("WARNING") for i in issues):
        logger.info("All validation checks passed!")

    return issues

# ============================================================
# SECTION 3: CANCELLATION ANALYSIS
# ============================================================

def identify_cancelled_services(calendar_dates_df):
    """
    Identify all cancelled services from calendar_dates
    exception type == 2 means service was removed/cancelled

    returns:
        pd.DataFrame: cancelled services with dates
    """
    cancellations = calendar_dates_df[
        calendar_dates_df['exception_type'] == 2
    ].copy()
    cancellations['day_of_week'] = cancellations['date'].dt.day_name()
    return cancellations

def map_cancellations_to_routes(cancellations_df, trips_df, routes_df):
    """
    Map cancelled service -> trips -> routes to find which Dublin Bus routes are most affected

    Returns:
        pd.DataFrame: Cancellations with route information
    """
    # Join cancellations -> tris via service_id
    cancel_trips =cancellations_df.merge(
        trips_df[['service_id', 'trip_id', 'route_id', 'trip_headsign']],
        on='service_id',
        how='inner'
    )

    # Join -> routes via route_id
    cancel_routes = cancel_trips.merge(
        routes_df[['route_id', 'route_short_name', 'route_long_name', 'agency_id']],
        on='route_id',
        how='inner'
    )

    return cancel_routes

def count_cancellations_by_route(cancel_routes_df):
    """
    Count cancellation by route headline finding

    returns:
        pd.DataFrame: routes ranked by number of cancellations
    """

    route_cancellations = (
        cancel_routes_df
        .groupby(['route_short_name', 'route_long_name'])
        .agg(
            total_cancelled_trips=('trip_id', 'nunique'),
            cancelled_dates=('date', 'nunique'),
        )
        .sort_values('total_cancelled_trips', ascending=False)
        .reset_index()
    )
    return route_cancellations

def calculate_expected_vs_cancelled(calendar_df, calendar_dates_df,trips_df, routes_df):
    """
    For each Dublin Bus route, calculate:
    Total EXPECTED trips (from calendar)
    Total CANCELLED trips (from calendar_dates, type 2)
    Cancellation rate (%)

    Key metric for answering the question of cancellations
    """

    # Get all dublin bus service_ids
    dublin_routes = routes_df[routes_df['agency_df'].isin({'7778019', '7778002', '7778021'})]
    dublin_trips = trips_df[trips_df['route_id'].isin(dublin_routes['route_id'])]

    # count expected operating days per service
    day_cols = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    results = []
    for _, service in calendar_df.iterrows():
        sid = service['service_id']
       
        trip_count = dublin_trips[dublin_trips['service_id'] == sid].shape[0]
        if trip_count == 0:
            continue 

        # count scheduled operating days using numpy
        date_range = pd.date_range(service['start_date'], service['end_date'])
        operating_days = np.zeros(len(date_range), dtype=bool)
        for i, day in enumerate(day_cols):
            if service[day] == 1:
                operating_days |= (date_range.dayofweek == i)

        # Count cancellations for this service
        service_cancellations = calendar_dates_df[
            (calendar_dates_df['service_id'] == sid) &
            (calendar_dates_df['exception_type'] == 2)
        ]

        total_scheduled = int(operating_days.sum()) * trip_count
        total_cancelled = len(service_cancellations) * trip_count

        results.append({
            'service_id': sid,
            'trip_count': trip_count,
            'scheduled_days': int(operating_days.sum()),
            'cancelled_days': len(service_cancellations),
            'total_scheduled_trips': total_scheduled,
            'total_cancelled_trips': total_cancelled,
        })

    results_df = pd.DataFrame(results)
    results_df['cancellation_rate'] = (
        results_df['total_cancelled_trips'] / results_df['total_scheduled_trips'] * 100
    ).round(2)

    return results_df

def cancellations_by_day_of_week(cancel_routes_df):
    """Aggregate cancellations by day of week using NumPy."""
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    by_day = (
        cancel_routes_df
        .groupby('day_of_week')['trip_id']
        .nunique()
        .reindex(day_order)
        .fillna(0)
        .astype(int)
    )
    return by_day

# Test

if __name__ == '__main__':
    data = load_all_data()

    # Filter to Dublin Bus
    dublin_routes = filter_dublin_bus_routes(data['routes'])
    dublin_trips = filter_dublin_trips(data['trips'], dublin_routes)

    # Clean stop times
    data['stop_times'] = clean_stop_times(data['stop_times'])

    # Validate
    issues = validate_data(data)

    # Cancellation Analysis
    cancellations = identify_cancelled_services(data['calendar_dates'])
    cancel_routes = map_cancellations_to_routes(cancellations, dublin_trips, dublin_routes)
    route_rankings = count_cancellations_by_route(cancel_routes)
    day_patterns = cancellations_by_day_of_week(cancel_routes)

    # Print results
    print("\nTop 10 Most Cancelled Routes:")
    print("=" * 60)
    print(route_rankings.head(10).to_string(index=False))

    print("\nCancellations by Day of Week:")
    print("-" * 40)
    print(day_patterns.to_string())
    