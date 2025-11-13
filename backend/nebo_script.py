import time
import hashlib
import requests
import pandas as pd
import os
import io
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from datetime import datetime, timezone


TOKEN = "6YjDzKZDjFRgfNFquSfzQox6"
CODE = "d5KV5Ha1zyowUey5JpAUG68S"   

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)

def get_auth_params(code):
    current_time = int(time.time())
    concat_str = f"{current_time}{code}"
    sha1_hash = hashlib.sha1(concat_str.encode('utf-8')).hexdigest()
    hash_part = sha1_hash[5:16]
    return current_time, hash_part

def download_latest_sensor_data(token, code, sensor_slug):
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
            print(f"Error uploading to Google Drive: {e}")

sensor_slugs = [
    "b4e8bdc2-5912-42d8-a032-0b48835a6bc1",
    "cb54c62e-3e12-4eee-9ced-5ba38ec98326",
    "df2378c8-e12c-406e-a38a-c2fd3db0509b"
]

# # Google Drive setup
# gauth = GoogleAuth()
# gauth.LoadClientConfigFile("client_secret.json")
# if gauth.credentials is None or gauth.access_token_expired:
#     gauth.LocalWebserverAuth() # Creates local webserver and auto handles authentication.

settings = {
    "client_config_backend": "service",
    "service_config": {
        "client_json_file_path": f"{script_dir}/service_account.json"
    }
}
gauth = GoogleAuth(settings=settings)
gauth.ServiceAuth()
drive = GoogleDrive(gauth)

# Specify your Google Drive folder ID here
# You can find this in the URL when you open the folder in Google Drive
GOOGLE_DRIVE_FOLDER_ID = '1KLu7ZRKxEDWr2kqT1aQ5aIJeJ-qnFN41' # Replace with your actual folder ID


# Run until 'exit' is typed or Ctrl+C is pressed
try:
    while True:
        for slug in sensor_slugs:
            filename = f"{slug}_minute_history.csv"
            data = download_latest_sensor_data(TOKEN, CODE, slug)

            if data:
                # Pass drive and folder_id to save to Google Drive
                merge_and_save_data(data, filename, drive=drive, folder_id=GOOGLE_DRIVE_FOLDER_ID)
                # If you also want to save locally, you can call merge_and_save_data(data, filename) again without drive arguments
            else:
                print(f"No data for {slug} at this cycle.")
        print("Sleeping for 2 minutes before next fetch cycle... (Type 'exit' and press Enter to stop)")
        time.sleep(2 * 60)

except KeyboardInterrupt:
    print("\nScript terminated by user (Ctrl+C).")