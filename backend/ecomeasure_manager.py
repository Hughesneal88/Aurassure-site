"""
Ecomeasure Data Manager - Handles data retrieval from Ecomeasure API
"""
import os
from datetime import datetime, timedelta
from ecomeasure import get_device_data, get_sensors_by_id, DEFAULT_SENSOR_IDS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if Ecomeasure token is configured
ECOMEASURE_TOKEN = os.environ.get('ECOMEASURE_TOKEN')
ECOMEASURE_ENABLED = bool(ECOMEASURE_TOKEN)


def get_ecomeasure_sensors():
    """
    Return list of available Ecomeasure sensors
    """
    if not ECOMEASURE_ENABLED:
        return []
    
    try:
        # Get sensor details from API
        sensors_data = get_sensors_by_id()
        
        if not sensors_data:
            # Fallback to default sensor IDs if API call fails
            sensors = []
            for sensor_id in DEFAULT_SENSOR_IDS:
                sensors.append({
                    "id": sensor_id,
                    "name": f"Ecomeasure Sensor {sensor_id}"
                })
            return sensors
        
        # Parse sensor details from API response
        sensors = []
        if isinstance(sensors_data, list):
            for sensor in sensors_data:
                sensors.append({
                    "id": sensor.get('id', sensor.get('sensor_id')),
                    "name": sensor.get('name', f"Ecomeasure Sensor {sensor.get('id', sensor.get('sensor_id'))}")
                })
        elif isinstance(sensors_data, dict):
            # Handle dict response format
            for sensor_id in DEFAULT_SENSOR_IDS:
                sensors.append({
                    "id": sensor_id,
                    "name": f"Ecomeasure Sensor {sensor_id}"
                })
        
        return sensors if sensors else []
    
    except Exception as e:
        print(f"Error fetching Ecomeasure sensors: {e}")
        # Return default sensors as fallback
        return [{"id": sid, "name": f"Ecomeasure Sensor {sid}"} for sid in DEFAULT_SENSOR_IDS]


def download_ecomeasure_data(sensor_ids=None, start_time=None, end_time=None):
    """
    Download Ecomeasure data for specified sensors and time range
    
    Args:
        sensor_ids: List of sensor IDs to retrieve, or None for all sensors
        start_time: datetime object for start of time range
        end_time: datetime object for end of time range
    
    Returns:
        DataFrame with sensor data
    """
    if not ECOMEASURE_ENABLED:
        print("Ecomeasure integration not enabled. Please set ECOMEASURE_TOKEN environment variable.")
        return None
    
    try:
        import pandas as pd
        
        # Determine which sensors to fetch
        if sensor_ids is None or sensor_ids == 'all':
            sensor_ids_to_fetch = DEFAULT_SENSOR_IDS
        else:
            if isinstance(sensor_ids, list):
                sensor_ids_to_fetch = [int(sid) for sid in sensor_ids]
            else:
                sensor_ids_to_fetch = [int(sensor_ids)]
        
        # Convert datetime to ISO format strings with Z suffix
        start_iso = None
        end_iso = None
        
        if start_time:
            start_iso = start_time.isoformat().replace('+00:00', 'Z')
            if not start_iso.endswith('Z'):
                start_iso += 'Z'
        
        if end_time:
            end_iso = end_time.isoformat().replace('+00:00', 'Z')
            if not end_iso.endswith('Z'):
                end_iso += 'Z'
        
        # Fetch data from Ecomeasure API
        data = get_device_data(
            sensor_ids=sensor_ids_to_fetch,
            start=start_iso,
            end=end_iso
        )
        
        if not data:
            print("No data retrieved from Ecomeasure API")
            return None
        
        # Process the data into a DataFrame
        all_dataframes = []
        
        for sensor_key, sensor_data in data.items():
            if sensor_data is None:
                print(f"No data for {sensor_key}")
                continue
            
            try:
                # Extract sensor ID from key (e.g., "sensor_20053" -> 20053)
                sensor_id = sensor_key.replace('sensor_', '')
                
                # Handle different response formats
                measurements = []
                if isinstance(sensor_data, dict):
                    # Check for common API response structures
                    if 'results' in sensor_data:
                        measurements = sensor_data['results']
                    elif 'measurements' in sensor_data:
                        measurements = sensor_data['measurements']
                    elif 'data' in sensor_data:
                        measurements = sensor_data['data']
                    else:
                        # Treat the dict itself as a single measurement
                        measurements = [sensor_data]
                elif isinstance(sensor_data, list):
                    measurements = sensor_data
                
                if measurements:
                    df = pd.DataFrame(measurements)
                    df['sensor_id'] = sensor_id
                    
                    # Convert timestamp columns to datetime
                    for col in ['timestamp', 'time', 'datetime', 'date']:
                        if col in df.columns:
                            try:
                                df[col] = pd.to_datetime(df[col])
                            except:
                                pass
                    
                    all_dataframes.append(df)
                    print(f"Successfully retrieved {len(df)} records from Ecomeasure sensor {sensor_id}")
            
            except Exception as e:
                print(f"Error processing data for {sensor_key}: {e}")
                continue
        
        # Combine all dataframes
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            print(f"Total records retrieved from Ecomeasure: {len(combined_df)}")
            return combined_df
        else:
            print("No data retrieved from any Ecomeasure sensor")
            return None
    
    except Exception as e:
        print(f"Error downloading Ecomeasure data: {e}")
        import traceback
        traceback.print_exc()
        return None
