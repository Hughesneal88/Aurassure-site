"""
Nebo Data Manager - Handles periodic data collection and retrieval from Google Drive
"""
import time
import hashlib
import requests
import pandas as pd
import os
import io
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from datetime import datetime, timezone

# Nebo API credentials
TOKEN = "6YjDzKZDjFRgfNFquSfzQox6"
CODE = "d5KV5Ha1zyowUey5JpAUG68S"

# Google Drive folder ID for storing Nebo data
# IMPORTANT: When using a service account, the folder MUST be in a Shared Drive (Team Drive)
# Service accounts do not have storage quota for regular folders
# You can find this ID in the URL when you open the folder in Google Drive
# Example: https://drive.google.com/drive/folders/YOUR_FOLDER_ID
GOOGLE_DRIVE_FOLDER_ID = '1KLu7ZRKxEDWr2kqT1aQ5aIJeJ-qnFN41'

# Nebo sensor slugs
SENSOR_SLUGS = [
    "b4e8bdc2-5912-42d8-a032-0b48835a6bc1",
    "cb54c62e-3e12-4eee-9ced-5ba38ec98326",
    "df2378c8-e12c-406e-a38a-c2fd3db0509b"
]

# Sensor metadata
SENSOR_METADATA = {
    "b4e8bdc2-5912-42d8-a032-0b48835a6bc1": {"name": "Nebo Sensor 1", "slug": "b4e8bdc2-5912-42d8-a032-0b48835a6bc1"},
    "cb54c62e-3e12-4eee-9ced-5ba38ec98326": {"name": "Nebo Sensor 2", "slug": "cb54c62e-3e12-4eee-9ced-5ba38ec98326"},
    "df2378c8-e12c-406e-a38a-c2fd3db0509b": {"name": "Nebo Sensor 3", "slug": "df2378c8-e12c-406e-a38a-c2fd3db0509b"}
}

script_dir = os.path.dirname(os.path.abspath(__file__))


def get_auth_params(code):
    """Generate authentication parameters for Nebo API"""
    current_time = int(time.time())
    concat_str = f"{current_time}{code}"
    sha1_hash = hashlib.sha1(concat_str.encode('utf-8')).hexdigest()
    hash_part = sha1_hash[5:16]
    return current_time, hash_part


def download_latest_sensor_data(token, code, sensor_slug):
    """Download latest sensor data from Nebo API"""
    base_url = "https://nebo.live/api/v2/sensors"
    url = f"{base_url}/{sensor_slug}/minute"
    t, h = get_auth_params(code)
    headers = {"X-Auth-Nebo": token}
    params = {"time": t, "hash": h}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"Latest sensor data for {sensor_slug} retrieved successfully at {datetime.now(timezone.utc)}")
            return data
        else:
            print(f"Failed to retrieve sensor data for {sensor_slug}. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error retrieving data for {sensor_slug}: {e}")
        return None


def merge_and_save_data(new_data, filename, drive=None, folder_id=None):
    """Merge new data with existing data and save to CSV and Google Drive"""
    if isinstance(new_data, dict) and 'data' in new_data:
        records = new_data['data']
    else:
        records = new_data

    if not records:
        print(f"No new data to save for {filename}")
        return

    new_df = pd.DataFrame(records)
    old_df = None

    # If Google Drive integration is enabled, download existing data from Drive first
    if drive and folder_id:
        try:
            file_list = drive.ListFile({'q': f"'{folder_id}' in parents and title='{filename}' and trashed=false"}).GetList()
            if file_list:
                # Download existing data from Google Drive
                file = file_list[0]
                content = file.GetContentString()
                old_df = pd.read_csv(io.StringIO(content))
                print(f"Downloaded existing data from Google Drive: {filename}")
        except Exception as e:
            print(f"Error downloading from Google Drive: {e}")
            old_df = None

    # If we didn't get data from Drive, try local file
    if old_df is None and os.path.exists(filename):
        # Read the existing local file
        old_df = pd.read_csv(filename)
        print(f"Loaded existing local data: {filename}")

    # Merge with existing data if available
    if old_df is not None:
        # Merge the new data with the old data
        combined_df = pd.concat([old_df, new_df], ignore_index=True)
        # Drop duplicates across all columns
        combined_df = combined_df.drop_duplicates(keep='last')
        # Save the merged data back to the file
        combined_df.to_csv(filename, index=False)
    else:
        # If no existing data, save the new data directly
        new_df.to_csv(filename, index=False)

    print(f"Data saved to {filename}")

    # If Google Drive integration is enabled, upload the file
    if drive and folder_id:
        try:
            file_list = drive.ListFile({'q': f"'{folder_id}' in parents and title='{filename}' and trashed=false"}).GetList()
            if file_list:
                # If the file already exists, update its content
                file = file_list[0]
                file.SetContentFile(filename)
                file.Upload()
                print(f"File updated on Google Drive: {filename}")
            else:
                # If the file doesn't exist, create a new one
                file = drive.CreateFile({'title': filename, 'parents': [{'id': folder_id}]})
                file.SetContentFile(filename)
                file.Upload()
                print(f"File uploaded to Google Drive: {filename}")
        except Exception as e:
            error_msg = str(e)
            print(f"Error uploading to Google Drive: {e}")
            if "Service Accounts do not have storage quota" in error_msg or "quotaExceeded" in error_msg:
                print("=" * 80)
                print("IMPORTANT: Service accounts require files to be stored in a Shared Drive!")
                print("Please ensure that the GOOGLE_DRIVE_FOLDER_ID points to a folder in a Shared Drive.")
                print("Regular folders won't work with service accounts.")
                print("Learn more: https://developers.google.com/workspace/drive/api/guides/about-shareddrives")
                print("=" * 80)


def get_drive_instance():
    """Initialize and return a Google Drive instance"""
    settings = {
        "client_config_backend": "service",
        "service_config": {
            "client_json_file_path": f"{script_dir}/service_account.json",
            "client_user_email": None
        },
        "oauth_scope": [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file"
        ]
    }
    gauth = GoogleAuth(settings=settings)
    gauth.ServiceAuth()
    return GoogleDrive(gauth)


def collect_nebo_data():
    """Collect data from all Nebo sensors and save to Google Drive"""
    try:
        drive = get_drive_instance()
        
        for slug in SENSOR_SLUGS:
            filename = f"{slug}_minute_history.csv"
            local_filepath = os.path.join(script_dir, filename)
            data = download_latest_sensor_data(TOKEN, CODE, slug)

            if data:
                merge_and_save_data(data, local_filepath, drive=drive, folder_id=GOOGLE_DRIVE_FOLDER_ID)
            else:
                print(f"No data for {slug} at this cycle.")
        
        print(f"Nebo data collection completed at {datetime.now(timezone.utc)}")
    except Exception as e:
        print(f"Error in collect_nebo_data: {e}")


def get_nebo_sensors():
    """Return list of available Nebo sensors"""
    return [
        {
            "slug": slug,
            "name": SENSOR_METADATA[slug]["name"]
        }
        for slug in SENSOR_SLUGS
    ]


def download_nebo_data_from_drive(sensor_slugs=None, start_time=None, end_time=None):
    """
    Download and filter Nebo data from Google Drive
    
    Args:
        sensor_slugs: List of sensor slugs to retrieve, or None for all sensors
        start_time: datetime object for start of time range
        end_time: datetime object for end of time range
    
    Returns:
        DataFrame with filtered sensor data
    """
    try:
        drive = get_drive_instance()
        
        # If no sensors specified, use all
        if sensor_slugs is None or sensor_slugs == 'all':
            sensor_slugs = SENSOR_SLUGS
        
        all_data = []
        
        for slug in sensor_slugs:
            filename = f"{slug}_minute_history.csv"
            
            # Find the file in Google Drive
            file_list = drive.ListFile({
                'q': f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and title='{filename}' and trashed=false"
            }).GetList()
            
            if not file_list:
                print(f"File not found in Google Drive: {filename}")
                continue
            
            # Download the file content
            file = file_list[0]
            content = file.GetContentString()
            
            # Read CSV data
            df = pd.read_csv(io.StringIO(content))
            
            # Add sensor slug to the dataframe
            df['sensor_slug'] = slug
            df['sensor_name'] = SENSOR_METADATA[slug]["name"]
            
            # Filter by time range if provided
            if 'timestamp' in df.columns:
                # Convert timestamp column to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                if start_time:
                    df = df[df['timestamp'] >= start_time]
                if end_time:
                    df = df[df['timestamp'] <= end_time]
            
            all_data.append(df)
        
        if not all_data:
            return None
        
        # Combine all sensor data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by timestamp if available
        if 'timestamp' in combined_df.columns:
            combined_df = combined_df.sort_values('timestamp')
        
        return combined_df
    
    except Exception as e:
        print(f"Error downloading Nebo data from Drive: {e}")
        return None
