"""
AirVisual Data Manager - Handles data retrieval from AirVisual/IQAir API
"""
import os
from datetime import datetime
from airvisual import (
    get_all_historical_data,
    DEVICES
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AirVisual doesn't require authentication for the device endpoints being used
# The devices are accessed directly via their public URLs
AIRVISUAL_ENABLED = True


def get_airvisual_sensors():
    """
    Return list of available AirVisual sensors
    """
    sensors = []
    for device_id, device_url in DEVICES.items():
        sensors.append({
            "id": device_id,
            "name": f"AirVisual {device_id}",
            "url": device_url
        })
    
    return sensors


def download_airvisual_data(sensor_ids=None, start_time=None, end_time=None):
    """
    Download AirVisual data for specified sensors
    
    Note: AirVisual API provides historical data but doesn't support custom time ranges
    in the current implementation. It returns all available historical data.
    
    Args:
        sensor_ids: List of sensor IDs (device IDs) to retrieve, or None for all sensors
        start_time: datetime object for start of time range (currently not used by API)
        end_time: datetime object for end of time range (currently not used by API)
    
    Returns:
        DataFrame with sensor data
    """
    if not AIRVISUAL_ENABLED:
        print("AirVisual integration not available.")
        return None
    
    try:
        import pandas as pd
        import json
        
        # Determine which sensors to fetch
        device_ids = []
        if sensor_ids is None or sensor_ids == 'all':
            device_ids = list(DEVICES.keys())
        else:
            if isinstance(sensor_ids, list):
                device_ids = sensor_ids
            else:
                device_ids = [sensor_ids]
        
        # Fetch data from each device
        all_dataframes = []
        for device_id in device_ids:
            if device_id not in DEVICES:
                print(f"Warning: Device {device_id} not found in DEVICES")
                continue
            
            try:
                # Fetch historical data for this device
                historical_data = get_all_historical_data(device_id)
                
                if historical_data and 'instant' in historical_data:
                    # Convert instant data to DataFrame
                    records = []
                    for record in historical_data['instant']:
                        # Flatten the nested structure
                        flat_record = {
                            'device_id': device_id,
                            'timestamp': record.get('ts'),
                            'pm25_aqius': record.get('pm25', {}).get('aqius'),
                            'pm25_conc': record.get('pm25', {}).get('conc'),
                            'temperature': record.get('tp'),
                            'humidity': record.get('hm')
                        }
                        records.append(flat_record)
                    
                    if records:
                        df = pd.DataFrame(records)
                        # Convert timestamp string to datetime
                        if 'timestamp' in df.columns:
                            df['timestamp'] = pd.to_datetime(df['timestamp'])
                        
                        # Filter by date range if provided
                        if start_time and 'timestamp' in df.columns:
                            df = df[df['timestamp'] >= start_time]
                        if end_time and 'timestamp' in df.columns:
                            df = df[df['timestamp'] <= end_time]
                        
                        all_dataframes.append(df)
                        print(f"Successfully retrieved {len(df)} records from AirVisual device {device_id}")
                else:
                    print(f"No historical data found for device {device_id}")
            
            except Exception as e:
                print(f"Error fetching data for device {device_id}: {e}")
                continue
        
        # Combine all dataframes
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            print(f"Total records retrieved from AirVisual: {len(combined_df)}")
            return combined_df
        else:
            print("No data retrieved from any AirVisual device")
            return None
    
    except Exception as e:
        print(f"Error downloading AirVisual data: {e}")
        import traceback
        traceback.print_exc()
        return None
