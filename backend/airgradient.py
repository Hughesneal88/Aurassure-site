import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import concurrent.futures
import pandas as pd
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from a .env file if present (project root or cwd)
_dotenv_path = find_dotenv(usecwd=True)
if _dotenv_path:
    load_dotenv(_dotenv_path)

API_URL = "https://api.airgradient.com/public/api/v1/locations/{locationId}/measures/past"

LOCATION_IDS = {
    "sensor_1": "170379",
    "sensor_2": "170380",
    "sensor_3": "170381"
}

# Maximum interval is 2 days (48 hours)
MAX_INTERVAL_HOURS = 48


def _build_auth_headers(
    token: Optional[str] = None,
    header_name: Optional[str] = None,
    scheme: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build authorization headers from explicit args or environment variables.
    Environment variables supported:
      - AIRGRADIENT_API_TOKEN / AIRGRADIENT_TOKEN / AIRGRADIENT_API_KEY
      - AIRGRADIENT_TOKEN_HEADER (default 'Authorization'; if API_KEY present defaults to 'x-api-key')
      - AIRGRADIENT_TOKEN_SCHEME (default 'Bearer')
    """
    resolved_token, resolved_header, resolved_scheme = _resolve_token_meta(token, header_name, scheme)

    if not resolved_token:
        return {}

    if resolved_header.lower() == "authorization":
        value = f"{resolved_scheme} {resolved_token}" if resolved_scheme else resolved_token
    else:
        value = resolved_token

    return {resolved_header: value}


def _resolve_token_meta(
    token: Optional[str] = None,
    header_name: Optional[str] = None,
    scheme: Optional[str] = None,
) -> tuple[Optional[str], str, Optional[str]]:
    """Resolve token, header name, and scheme from args/env for reuse."""
    resolved_token = (
        token
        or os.getenv("AIRGRADIENT_API_TOKEN")
        or os.getenv("AIRGRADIENT_TOKEN")
        or os.getenv("AIRGRADIENT_API_KEY")
    )

    # If user set API_KEY and no header name, prefer x-api-key, else Authorization
    default_header = (
        "x-api-key"
        if os.getenv("AIRGRADIENT_API_KEY") and not os.getenv("AIRGRADIENT_TOKEN_HEADER")
        else "Authorization"
    )
    resolved_header = header_name or os.getenv("AIRGRADIENT_TOKEN_HEADER", default_header)
    resolved_scheme = scheme if scheme is not None else os.getenv("AIRGRADIENT_TOKEN_SCHEME", "Bearer")
    return resolved_token, resolved_header, resolved_scheme


def iso_to_datetime(iso_string: str) -> datetime:
    """Convert ISO format string to datetime object"""
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))


def datetime_to_iso(dt: datetime) -> str:
    """Convert datetime object to ISO format string"""
    return dt.isoformat() + 'Z'


def split_date_range(start_iso: str, end_iso: str) -> List[tuple]:
    """
    Split a date range into 2-day intervals for API requests
    
    Args:
        start_iso: Start date in ISO format (e.g., '2025-12-19T00:00:00Z')
        end_iso: End date in ISO format
    
    Returns:
        List of tuples containing (from_iso, to_iso) for each interval
    """
    start = iso_to_datetime(start_iso[:-8])
    end = iso_to_datetime(end_iso[:-8])
    
    intervals = []
    current = start
    
    while current < end:
        interval_end = min(current + timedelta(hours=MAX_INTERVAL_HOURS), end)
        intervals.append((datetime_to_iso(current), datetime_to_iso(interval_end)))
        current = interval_end
    
    return intervals


def get_location_data(
    location_id: str,
    from_iso: str,
    to_iso: str,
    *,
    token: Optional[str] = None,
    header_name: Optional[str] = None,
    scheme: Optional[str] = None,
    use_header_auth: bool = False,
    include_token_in_query: bool = True,
    include_token_in_body: bool = False,
    query_token_param: str = "token",
    body_token_field: str = "token",
    method: Optional[str] = None,
) -> Optional[Dict]:
    """
    Fetch data for a single location within a 2-day interval
    
    Args:
        location_id: Location ID
        from_iso: Start date in ISO format
        to_iso: End date in ISO format
    
    Returns:
        Dictionary with API response or None if request fails
    """
    base_url = API_URL.format(locationId=location_id)
    
    headers = _build_auth_headers(token=token, header_name=header_name, scheme=scheme) if use_header_auth else None
    resolved_token, _, _ = _resolve_token_meta(token, header_name, scheme)

    # Build URL with token appended directly (not URL-encoded)
    if include_token_in_query and resolved_token:
        # print(resolved_token)
        url = f"{base_url}?from={from_iso}&to={to_iso}&token={resolved_token}"
    else:
        # print(resolved_token)
        url = f"{base_url}?from={from_iso}&to={to_iso}"

    # Decide method: if body token requested, default to POST; else GET unless overridden
    effective_method = (method or ("POST" if include_token_in_body else "GET")).upper()

    try:
        if effective_method == "POST":
            payload = {"from": from_iso, "to": to_iso}
            if include_token_in_body and resolved_token:
                payload[body_token_field] = resolved_token
            response = requests.post(url, json=payload, headers=headers or None, timeout=10)
        else:
            response = requests.get(url, headers=headers or None, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for location {location_id}: {e}")
        return None


def get_location_data_range(
    location_id: str,
    from_iso: str,
    to_iso: str,
    *,
    token: Optional[str] = None,
    header_name: Optional[str] = None,
    scheme: Optional[str] = None,
    use_header_auth: bool = False,
    include_token_in_query: bool = False,
    include_token_in_body: bool = False,
    query_token_param: str = "token",
    body_token_field: str = "token",
    method: Optional[str] = None,
) -> List[Dict]:
    """
    Fetch data for a location across multiple 2-day intervals (optimized with parallel requests)
    
    Args:
        location_id: Location ID
        from_iso: Start date in ISO format
        to_iso: End date in ISO format
    
    Returns:
        Combined list of all measurements
    """
    intervals = split_date_range(from_iso, to_iso)
    all_data = []
    
    print(f"Fetching data for location {location_id} across {len(intervals)} interval(s)...")
    
    # Use ThreadPoolExecutor for parallel requests to speed up the process
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(
                get_location_data,
                location_id,
                from_dt,
                to_dt,
                token=token,
                header_name=header_name,
                scheme=scheme,
                use_header_auth=use_header_auth,
                include_token_in_query=include_token_in_query,
                include_token_in_body=include_token_in_body,
                query_token_param=query_token_param,
                body_token_field=body_token_field,
                method=method,
            )
            for from_dt, to_dt in intervals
        ]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            if result:
                if isinstance(result, list):
                    all_data.extend(result)
                elif isinstance(result, dict) and 'data' in result:
                    all_data.extend(result['data'])
                print(f"✓ Interval {i}/{len(intervals)} completed")
            else:
                print(f"✗ Interval {i}/{len(intervals)} failed")
    
    return all_data


def get_all_sensors_data(
    sensor_names: Optional[List[str]] = None,
    from_iso: str = None,
    to_iso: str = None,
    *,
    token: Optional[str] = None,
    header_name: Optional[str] = None,
    scheme: Optional[str] = None,
    use_header_auth: bool = False,
    include_token_in_query: bool = True,
    include_token_in_body: bool = False,
    query_token_param: str = "token",
    body_token_field: str = "token",
    method: Optional[str] = None,
) -> Dict[str, List[Dict]]:
    """
    Fetch data from multiple sensors in parallel (fastest response)
    
    Args:
        sensor_names: List of sensor names (defaults to all available sensors)
        from_iso: Start date in ISO format (defaults to 2 days ago)
        to_iso: End date in ISO format (defaults to now)
    
    Returns:
        Dictionary mapping sensor names to their measurements
    """
    if sensor_names is None:
        sensor_names = list(LOCATION_IDS.keys())
    
    # Set default date range if not provided
    if to_iso is None:
        to_iso = datetime_to_iso(datetime.utcnow())
    if from_iso is None:
        from_iso = datetime_to_iso(datetime.utcnow() - timedelta(days=2))

    results = {}
    
    print(f"\nFetching data from {from_iso} to {to_iso}")
    print(f"Requesting data from sensors: {sensor_names}\n")
    
    # Parallel requests for all sensors
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(sensor_names)) as executor:
        futures = {
            executor.submit(
                get_location_data_range,
                LOCATION_IDS[sensor],
                from_iso,
                to_iso,
                token=token,
                header_name=header_name,
                scheme=scheme,
                use_header_auth=use_header_auth,
                include_token_in_query=include_token_in_query,
                include_token_in_body=include_token_in_body,
                query_token_param=query_token_param,
                body_token_field=body_token_field,
                method=method,
            ): sensor
            for sensor in sensor_names if sensor in LOCATION_IDS
        }
        
        for future in concurrent.futures.as_completed(futures):
            sensor = futures[future]
            data = future.result()
            results[sensor] = data
            print(f"✓ {sensor}: {len(data)} measurements retrieved")
    
    return results


def save_sensor_data(data: Dict[str, List[Dict]], filename: str = "airgradient_data.json") -> bool:
    """Save fetched data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Data saved to {filename}")
        return True
    except IOError as e:
        print(f"Error saving data: {e}")
        return False


def data_to_dataframe(data: Dict[str, List[Dict]]) -> Dict[str, pd.DataFrame]:
    """
    Convert sensor data to pandas DataFrames for easier analysis
    
    Args:
        data: Dictionary mapping sensor names to their measurements
    
    Returns:
        Dictionary mapping sensor names to pandas DataFrames
    """
    dataframes = {}
    
    for sensor, measurements in data.items():
        if measurements:
            df = pd.DataFrame(measurements)
            
            # Convert timestamp to datetime if present
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
            dataframes[sensor] = df
        else:
            dataframes[sensor] = pd.DataFrame()
    
    return dataframes


def get_combined_dataframe(data: Dict[str, List[Dict]]) -> pd.DataFrame:
    """
    Combine all sensor data into a single DataFrame with sensor identification
    
    Args:
        data: Dictionary mapping sensor names to their measurements
    
    Returns:
        Combined pandas DataFrame with 'sensor' column
    """
    all_dfs = []
    
    for sensor, measurements in data.items():
        if measurements:
            df = pd.DataFrame(measurements)
            df['sensor'] = sensor
            df['location_id'] = LOCATION_IDS.get(sensor, '')
            all_dfs.append(df)
    
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Convert timestamp to datetime if present
        if 'timestamp' in combined_df.columns:
            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            combined_df = combined_df.sort_values('timestamp')
        
        return combined_df
    
    return pd.DataFrame()


def analyze_sensor_data(df: pd.DataFrame, sensor_column: str = 'pm02') -> pd.DataFrame:
    """
    Perform statistical analysis on sensor data
    
    Args:
        df: DataFrame with sensor measurements
        sensor_column: Column to analyze (e.g., 'pm02', 'pm10', 'temperature')
    
    Returns:
        DataFrame with statistical summary by sensor
    """
    if df.empty or sensor_column not in df.columns:
        return pd.DataFrame()
    
    stats = df.groupby('sensor')[sensor_column].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('25%', lambda x: x.quantile(0.25)),
        ('50%', lambda x: x.quantile(0.50)),
        ('75%', lambda x: x.quantile(0.75)),
        ('max', 'max')
    ]).round(2)
    
    return stats


def get_latest_readings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the latest reading from each sensor
    
    Args:
        df: Combined DataFrame with timestamp column
    
    Returns:
        DataFrame with latest readings per sensor
    """
    if df.empty or 'timestamp' not in df.columns:
        return pd.DataFrame()
    
    return df.sort_values('timestamp').groupby('sensor').tail(1)


def display_sensor_summary(data: Dict[str, List[Dict]]) -> None:
    """Display a summary of the fetched data using pandas"""
    print("\n" + "="*50)
    print("SENSOR DATA SUMMARY")
    print("="*50)
    
    df = get_combined_dataframe(data)
    
    if df.empty:
        print("\nNo data available")
        return
    
    print(f"\nTotal measurements: {len(df)}")
    print(f"Sensors: {df['sensor'].unique().tolist()}")
    
    if 'timestamp' in df.columns:
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    print("\n" + "-"*50)
    print("LATEST READINGS:")
    print("-"*50)
    latest = get_latest_readings(df)
    print(latest.to_string(index=False))
    
    # Display statistics for PM2.5 if available
    if 'pm02' in df.columns:
        print("\n" + "-"*50)
        print("PM2.5 STATISTICS BY SENSOR:")
        print("-"*50)
        print(analyze_sensor_data(df, 'pm02'))


def save_to_csv(data: Dict[str, List[Dict]], filename: str = "airgradient_data.csv") -> bool:
    """
    Save sensor data to CSV file using pandas
    
    Args:
        data: Dictionary mapping sensor names to their measurements
        filename: Output CSV filename
    
    Returns:
        True if successful, False otherwise
    """
    try:
        df = get_combined_dataframe(data)
        if df.empty:
            print("No data to save")
            return False
        
        df.to_csv(filename, index=False)
        print(f"\n✓ Data saved to {filename} ({len(df)} records)")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False


# Example usage:
if __name__ == "__main__":
    # Option A) Use env vars, token goes in query by default
    #   PowerShell (Windows):
    #   $env:AIRGRADIENT_API_TOKEN = "<your-token>"
    #   # The token will be sent as a query parameter named 'token'.
    #   # To change the parameter name, pass query_token_param in the call.
    # print(os.getenv("AIRGRADIENT_API_KEY"))
    start = datetime.utcnow() - timedelta(days=70)
    data = get_all_sensors_data(token=os.getenv("AIRGRADIENT_API_KEY"), from_iso=start.isoformat() + 'Z', to_iso=datetime.utcnow().isoformat() + 'Z')
    
    # Save as JSON
    save_sensor_data(data)
    
    # Save as CSV (using pandas)
    save_to_csv(data)
    
    # Display summary with pandas analysis
    display_sensor_summary(data)
    
    # Get DataFrames for custom analysis
    dfs = data_to_dataframe(data)
    combined_df = get_combined_dataframe(data)
    
    # Analyze specific metrics
    pm25_stats = analyze_sensor_data(combined_df, 'pm02')
    latest = get_latest_readings(combined_df)

    # Option B) Explicit token + last-month example (30 days)
    # from_dt = datetime.utcnow() - timedelta(days=30)
    # to_dt = datetime.utcnow()
    # data_last_month = get_all_sensors_data(
    #     from_iso=datetime_to_iso(from_dt),
    #     to_iso=datetime_to_iso(to_dt),
    #     token="<your-token>",           # optional if .env is set
    #     # Query param is used by default; customize its name if needed:
    #     # query_token_param="api_key",
    #     # If your API requires token in POST body instead:
    #     # include_token_in_body=True,
    #     # body_token_field="api_key",
    #     # method="POST",
    # )
    # save_to_csv(data_last_month, filename="airgradient_last_month.csv")
    
    pass