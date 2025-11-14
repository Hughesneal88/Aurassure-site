"""
Crafted Climate Data Manager - Handles data retrieval from Crafted Climate API
"""
import os
import json
from datetime import datetime
from crafted_climate import get_cclimate_data
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Crafted Climate API credentials from environment variables
CRAFTED_CLIMATE_API_KEY = os.environ.get('CRAFTED_CLIMATE_API_KEY', '')
CRAFTED_CLIMATE_AUID = os.environ.get('CRAFTED_CLIMATE_AUID', '')

# Load AUIDs from configuration file
def load_auids_from_file():
    """
    Load Crafted Climate AUIDs from configuration file
    Returns list of AUID configurations or None if file doesn't exist
    """
    config_file = os.path.join(os.path.dirname(__file__), 'crafted_climate_auids.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('auids', [])
        except Exception as e:
            print(f"Error loading AUIDs from file: {e}")
            return None
    return None

# Try to load AUIDs from file, fallback to environment variable
CRAFTED_CLIMATE_AUIDS = load_auids_from_file()

# If no file exists, use environment variable (backward compatibility)
if CRAFTED_CLIMATE_AUIDS is None and CRAFTED_CLIMATE_AUID:
    CRAFTED_CLIMATE_AUIDS = [
        {
            "id": CRAFTED_CLIMATE_AUID,
            "name": f"Crafted Climate Sensor ({CRAFTED_CLIMATE_AUID})",
            "description": "Sensor from environment variable"
        }
    ]

# Check if Crafted Climate is enabled
CRAFTED_CLIMATE_ENABLED = bool(CRAFTED_CLIMATE_API_KEY and CRAFTED_CLIMATE_AUIDS)


def get_crafted_climate_sensors():
    """
    Return list of available Crafted Climate sensors
    Reads from configuration file or falls back to environment variable
    """
    if not CRAFTED_CLIMATE_ENABLED:
        return []
    
    sensors = []
    for auid_config in CRAFTED_CLIMATE_AUIDS:
        sensor = {
            "id": auid_config.get("id"),
            "name": auid_config.get("name", f"Crafted Climate Sensor ({auid_config.get('id')})")
        }
        if auid_config.get("description"):
            sensor["description"] = auid_config.get("description")
        sensors.append(sensor)
    
    return sensors


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
        print("Crafted Climate integration not enabled. Please set CRAFTED_CLIMATE_API_KEY and configure AUIDs.")
        return None
    
    try:
        import pandas as pd
        
        # Determine which AUIDs to fetch
        auids_to_fetch = []
        if sensor_ids is None or sensor_ids == 'all':
            # Fetch all configured AUIDs
            auids_to_fetch = [auid_config.get('id') for auid_config in CRAFTED_CLIMATE_AUIDS]
        else:
            # Use the specified sensor IDs
            if isinstance(sensor_ids, list):
                auids_to_fetch = sensor_ids
            else:
                auids_to_fetch = [sensor_ids]
        
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
        
        # Fetch data for each AUID and combine
        all_dataframes = []
        for auid in auids_to_fetch:
            try:
                # Find the sensor name from configuration
                sensor_name = f"Crafted Climate Sensor ({auid})"
                for auid_config in CRAFTED_CLIMATE_AUIDS:
                    if auid_config.get('id') == auid:
                        sensor_name = auid_config.get('name', sensor_name)
                        break
                
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
                    df['sensor_name'] = sensor_name
                    all_dataframes.append(df)
                    print(f"Successfully retrieved {len(df)} records from Crafted Climate for {auid}")
                else:
                    print(f"No data returned for AUID {auid}")
            except Exception as e:
                print(f"Error fetching data for AUID {auid}: {e}")
                continue
        
        # Combine all dataframes
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            print(f"Total records retrieved: {len(combined_df)}")
            return combined_df
        else:
            print("No data retrieved from any sensor")
            return None
    
    except Exception as e:
        print(f"Error downloading Crafted Climate data: {e}")
        return None
