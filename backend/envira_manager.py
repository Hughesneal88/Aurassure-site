"""
Envira Data Manager - Handles data retrieval from Envira IoT API
"""
import os
from datetime import datetime, timedelta
from envira import get_device_data
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Envira device UUIDs - these should be configured in environment or a config file
# Default devices from the example code
ENVIRA_DEVICES = {
    "device_1": os.environ.get('ENVIRA_DEVICE_1_UUID', 'fba1d9dd-5031-334d-4e2e-3120ff0f3429')
}

# Load additional devices from environment variables
for i in range(2, 10):  # Support up to 10 devices
    device_uuid = os.environ.get(f'ENVIRA_DEVICE_{i}_UUID')
    if device_uuid:
        ENVIRA_DEVICES[f"device_{i}"] = device_uuid

# Envira doesn't require authentication - it uses public device UUIDs
ENVIRA_ENABLED = bool(ENVIRA_DEVICES)


def get_envira_sensors():
    """
    Return list of available Envira sensors
    """
    if not ENVIRA_ENABLED:
        return []
    
    sensors = []
    for device_name, device_uuid in ENVIRA_DEVICES.items():
        sensors.append({
            "id": device_uuid,
            "name": f"Envira {device_name.replace('_', ' ').title()}",
            "uuid": device_uuid
        })
    
    return sensors


def download_envira_data(sensor_ids=None, start_time=None, end_time=None):
    """
    Download Envira data for specified sensors and time range
    
    Args:
        sensor_ids: List of sensor UUIDs to retrieve, or None for all sensors
        start_time: datetime object for start of time range
        end_time: datetime object for end of time range
    
    Returns:
        DataFrame with sensor data
    """
    if not ENVIRA_ENABLED:
        print("Envira integration not enabled. Please set ENVIRA_DEVICE_*_UUID environment variables.")
        return None
    
    try:
        import pandas as pd
        
        # Determine which devices to fetch
        device_uuids = {}
        if sensor_ids is None or sensor_ids == 'all':
            device_uuids = ENVIRA_DEVICES.copy()
        else:
            # Match sensor_ids to device UUIDs
            if isinstance(sensor_ids, list):
                for sid in sensor_ids:
                    # Check if it's a device name or UUID
                    if sid in ENVIRA_DEVICES:
                        device_uuids[sid] = ENVIRA_DEVICES[sid]
                    else:
                        # Assume it's a UUID
                        device_uuids[sid] = sid
            else:
                if sensor_ids in ENVIRA_DEVICES:
                    device_uuids[sensor_ids] = ENVIRA_DEVICES[sensor_ids]
                else:
                    device_uuids[sensor_ids] = sensor_ids
        
        # Convert datetime to ISO format strings
        start_iso = None
        end_iso = None
        
        if start_time:
            start_iso = start_time.isoformat()
        if end_time:
            end_iso = end_time.isoformat()
        
        # Fetch data from each device
        all_dataframes = []
        for device_name, device_uuid in device_uuids.items():
            try:
                # Fetch data from Envira API
                data = get_device_data(device_uuid, start_iso, end_iso)
                
                if data and isinstance(data, dict) and 'data' in data:
                    measurements = data.get('data', [])
                    if measurements:
                        df = pd.DataFrame(measurements)
                        df['device_uuid'] = device_uuid
                        df['device_name'] = device_name
                        
                        # Convert timestamp if present
                        if 'timestamp' in df.columns:
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        elif 'ts' in df.columns:
                            df['timestamp'] = pd.to_datetime(df['ts'], unit='ms')
                            df = df.drop('ts', axis=1)
                        
                        all_dataframes.append(df)
                        print(f"Successfully retrieved {len(df)} records from Envira device {device_name}")
                else:
                    print(f"No data found for Envira device {device_name}")
            
            except Exception as e:
                print(f"Error fetching data for Envira device {device_name}: {e}")
                continue
        
        # Combine all dataframes
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            print(f"Total records retrieved from Envira: {len(combined_df)}")
            return combined_df
        else:
            print("No data retrieved from any Envira device")
            return None
    
    except Exception as e:
        print(f"Error downloading Envira data: {e}")
        import traceback
        traceback.print_exc()
        return None
