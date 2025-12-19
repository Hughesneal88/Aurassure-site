"""
AirGradient Data Manager - Handles data retrieval from AirGradient API
"""
import os
from datetime import datetime
from airgradient import (
    get_all_sensors_data,
    get_combined_dataframe,
    LOCATION_IDS
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AirGradient API token from environment variables
AIRGRADIENT_API_TOKEN = os.environ.get('AIRGRADIENT_API_TOKEN') or os.environ.get('AIRGRADIENT_API_KEY')

# Check if AirGradient is enabled
AIRGRADIENT_ENABLED = bool(AIRGRADIENT_API_TOKEN)


def get_airgradient_sensors():
    """
    Return list of available AirGradient sensors
    """
    if not AIRGRADIENT_ENABLED:
        return []
    
    sensors = []
    for sensor_name, location_id in LOCATION_IDS.items():
        sensors.append({
            "id": sensor_name,
            "name": f"AirGradient {sensor_name.replace('_', ' ').title()}",
            "location_id": location_id
        })
    
    return sensors


def download_airgradient_data(sensor_ids=None, start_time=None, end_time=None):
    """
    Download AirGradient data for specified sensors and time range
    
    Args:
        sensor_ids: List of sensor IDs to retrieve, or None for all sensors
        start_time: datetime object for start of time range
        end_time: datetime object for end of time range
    
    Returns:
        DataFrame with sensor data
    """
    if not AIRGRADIENT_ENABLED:
        print("AirGradient integration not enabled. Please set AIRGRADIENT_API_TOKEN or AIRGRADIENT_API_KEY.")
        return None
    
    try:
        import pandas as pd
        
        # Determine which sensors to fetch
        sensor_names = None
        if sensor_ids is not None and sensor_ids != 'all':
            if isinstance(sensor_ids, list):
                sensor_names = sensor_ids
            else:
                sensor_names = [sensor_ids]
        
        # Convert datetime to ISO format strings
        from_iso = None
        to_iso = None
        
        if start_time:
            from_iso = start_time.isoformat() + 'Z'
        if end_time:
            to_iso = end_time.isoformat() + 'Z'
        
        # Fetch data from AirGradient API
        data = get_all_sensors_data(
            sensor_names=sensor_names,
            from_iso=from_iso,
            to_iso=to_iso,
            token=AIRGRADIENT_API_TOKEN,
            include_token_in_query=True
        )
        
        if not data:
            print("No data returned from AirGradient API")
            return None
        
        # Convert to DataFrame
        df = get_combined_dataframe(data)
        
        if df is not None and not df.empty:
            print(f"Successfully retrieved {len(df)} records from AirGradient")
            return df
        else:
            print("No data retrieved from AirGradient")
            return None
    
    except Exception as e:
        print(f"Error downloading AirGradient data: {e}")
        import traceback
        traceback.print_exc()
        return None
