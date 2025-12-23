import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()
ECOMEASURE_TOKEN = os.getenv('ECOMEASURE_TOKEN')
BASE_URL = "https://airlab-ws.i-comesure.com/api/"

# Default sensor IDs (can be overridden in function calls)
DEFAULT_SENSOR_IDS = [20053, 20055, 20054]


def get_sensors_by_id(sensor_ids: Optional[List[int]] = None) -> Optional[Dict]:
    """
    Retrieve sensor details for a list of sensor IDs
    
    Args:
        sensor_ids: List of sensor IDs (max 10 per request). Defaults to DEFAULT_SENSOR_IDS.
    
    Returns:
        Dictionary with sensor details or None if request fails
    """
    if sensor_ids is None:
        sensor_ids = DEFAULT_SENSOR_IDS
    
    # Validate sensor ID count (max 10)
    if len(sensor_ids) > 10:
        print("Warning: Maximum 10 sensor IDs allowed per request. Using first 10.")
        sensor_ids = sensor_ids[:10]
    
    headers = {
        'Authorization': f'TOKEN {ECOMEASURE_TOKEN}'
    }
    
    # Format sensor IDs as comma-separated string for URL path
    id_list_str = ','.join(str(sid) for sid in sensor_ids)
    url = f"{BASE_URL}group/sensors/{id_list_str}"
    
    print(f"Request URL: {url}")
    
    try:
        # Use GET request to retrieve sensor details
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sensors = response.json()
        print(f"✓ Retrieved sensor details")
        return sensors
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sensor details: {e}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
        return None





def get_device_data(
    sensor_ids: Optional[List[int]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    unit: bool = False
) -> Optional[Dict]:
    """
    Fetch data from Ecomeasure API for multiple sensors (one at a time)
    
    Args:
        sensor_ids: List of sensor IDs. Defaults to DEFAULT_SENSOR_IDS.
        start: Start date in ISO 8601 format (e.g., '2025-12-22T00:00:00Z'). 
               Defaults to 24 hours ago if None.
        end: End date in ISO 8601 format. Defaults to now if None.
        limit: Number of measurements to display on a single page
        offset: Number of measurements to skip
        unit: Display measurement units if True
    
    Returns:
        Dictionary with API response or None if request fails
    """
    if sensor_ids is None:
        sensor_ids = DEFAULT_SENSOR_IDS
    
    headers = {
        'Authorization': f'TOKEN {ECOMEASURE_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Set default timestamps in ISO 8601 format
    if end is None:
        end = datetime.utcnow().isoformat() + 'Z'
    
    if start is None:
        # Default to 24 hours ago
        start_dt = datetime.utcnow() - timedelta(hours=24)
        start = start_dt.isoformat() + 'Z'
    
    # Collect data from each sensor individually
    all_data = {}
    
    for sensor_id in sensor_ids:
        url = f"{BASE_URL}sensors/{sensor_id}/measurements/"
        
        # Build query parameters
        params = {
            'start': start,
            'end': end,
            'unit': str(unit).lower()  # Convert to "true" or "false" string
        }
        
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        
        print(f"Request URL: {url}")
        print(f"Parameters: {json.dumps(params, indent=2)}")
        
        try:
            # Use GET request with parameters in query string
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            sensor_data = response.json()
            all_data[f"sensor_{sensor_id}"] = sensor_data
            print(f"✓ Retrieved data for sensor {sensor_id}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for sensor {sensor_id}: {e}")
            if 'response' in locals():
                print(f"Response content: {response.text}")
            all_data[f"sensor_{sensor_id}"] = None
    
    return all_data


def get_sensors_dataframe(
    sensor_ids: Optional[List[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    unit: bool = False
) -> Optional[pd.DataFrame]:
    """
    Fetch sensor data and return as a pandas DataFrame
    
    Args:
        sensor_ids: List of sensor IDs
        start: Start date in ISO 8601 format
        end: End date in ISO 8601 format
        limit: Number of measurements per page
        offset: Number of measurements to skip
        unit: Display measurement units
    
    Returns:
        pandas DataFrame with sensor measurements or None if failed
    """
    data = get_device_data(sensor_ids, start, end, limit, offset, unit)
    
    if data is None:
        return None
    
    # Convert to DataFrame (structure depends on API response)
    # Adjust based on actual API response structure
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict) and 'results' in data:
        df = pd.DataFrame(data['results'])
    else:
        df = pd.DataFrame([data])
    
    return df


def save_to_json(data: Dict, filename: str = "ecomeasure_data.json") -> bool:
    """Save fetched data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Data saved to {filename}")
        return True
    except IOError as e:
        print(f"Error saving data: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # First, get sensor details for specific IDs
    print("=" * 60)
    print("SENSOR DETAILS")
    print("=" * 60)
    sensor_details = get_sensors_by_id()
    
    if sensor_details:
        print("\n" + json.dumps(sensor_details, indent=2)[:500] + "..." if len(str(sensor_details)) > 500 else json.dumps(sensor_details, indent=2))
    
    print("\n" + "=" * 60)
    print("FETCHING SENSOR MEASUREMENTS")
    print("=" * 60)
    
    # Test with default sensors (last 24 hours)
    print("Fetching data from Ecomeasure API...")
    data = get_device_data()
    
    if data:
        print("\n✓ Success! Data retrieved:")
        print(json.dumps(data, indent=2)[:500] + "..." if len(str(data)) > 500 else json.dumps(data, indent=2))
        
        # Save to file
        save_to_json(data)
        
        # Try converting to DataFrame
        df = get_sensors_dataframe()
        if df is not None:
            print(f"\n✓ DataFrame created with {len(df)} rows")
            print(df.head())
    else:
        print("\n✗ Failed to retrieve data")
    
    # Example: Custom date range (last 7 days)
    # from datetime import datetime, timedelta
    # end_dt = datetime.utcnow()
    # start_dt = end_dt - timedelta(days=7)
    # data = get_device_data(
    #     sensor_ids=[1087, 862, 786],
    #     start=start_dt.isoformat() + 'Z',
    #     end=end_dt.isoformat() + 'Z',
    #     unit=True
    # )