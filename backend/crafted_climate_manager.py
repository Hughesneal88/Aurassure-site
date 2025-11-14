"""
Crafted Climate Data Manager - Handles data retrieval from Crafted Climate API
"""
import os
from datetime import datetime
from crafted_climate import get_cclimate_data
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Crafted Climate API credentials from environment variables
CRAFTED_CLIMATE_API_KEY = os.environ.get('CRAFTED_CLIMATE_API_KEY', '')
CRAFTED_CLIMATE_AUID = os.environ.get('CRAFTED_CLIMATE_AUID', '')

# Check if Crafted Climate is enabled
CRAFTED_CLIMATE_ENABLED = bool(CRAFTED_CLIMATE_API_KEY and CRAFTED_CLIMATE_AUID)


def get_crafted_climate_sensors():
    """
    Return list of available Crafted Climate sensors
    For now, returning a single sensor based on AUID
    """
    if not CRAFTED_CLIMATE_ENABLED:
        return []
    
    return [
        {
            "id": CRAFTED_CLIMATE_AUID,
            "name": f"Crafted Climate Sensor ({CRAFTED_CLIMATE_AUID})"
        }
    ]


def download_crafted_climate_data(sensor_ids=None, start_time=None, end_time=None):
    """
    Download Crafted Climate data for specified sensors and time range
    
    Args:
        sensor_ids: List of sensor IDs (AUIDs) to retrieve, or None for all sensors
        start_time: datetime object for start of time range
        end_time: datetime object for end of time range
    
    Returns:
        DataFrame with sensor data
    """
    if not CRAFTED_CLIMATE_ENABLED:
        print("Crafted Climate integration not enabled. Please set CRAFTED_CLIMATE_API_KEY and CRAFTED_CLIMATE_AUID.")
        return None
    
    try:
        # If no sensors specified or 'all', use the configured AUID
        if sensor_ids is None or sensor_ids == 'all':
            auid = CRAFTED_CLIMATE_AUID
        else:
            # Use the first sensor ID provided
            auid = sensor_ids[0] if isinstance(sensor_ids, list) else sensor_ids
        
        # Format dates for the API (YYYY-MM-DD format)
        start_date = start_time.strftime('%Y-%m-%d') if start_time else None
        end_date = end_time.strftime('%Y-%m-%d') if end_time else None
        
        # If no dates provided, use a reasonable default (last 7 days)
        if not start_date or not end_date:
            from datetime import timedelta
            end = datetime.now()
            start = end - timedelta(days=7)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        # Fetch data from Crafted Climate API
        df = get_cclimate_data(
            start_date=start_date,
            end_date=end_date,
            api_key=CRAFTED_CLIMATE_API_KEY,
            auid=auid
        )
        
        if df is not None and not df.empty:
            # Add sensor information to the dataframe
            df['sensor_id'] = auid
            df['sensor_name'] = f"Crafted Climate Sensor ({auid})"
            print(f"Successfully retrieved {len(df)} records from Crafted Climate")
        
        return df
    
    except Exception as e:
        print(f"Error downloading Crafted Climate data: {e}")
        return None
