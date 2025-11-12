api_url = "https://app.aurassure.com/-/api/iot-platform/v1.1.0"
import requests
import json
from datetime import datetime, timedelta
# from requests.auth import HTTPBasicAuth
import pandas as pd

import os
from dotenv import load_dotenv
load_dotenv()


AccessId = os.getenv("AccessId")
AccessKey = os.getenv("AccessKey")



def get_data(sensors=all, start_time=None, end_time=None, save_to=None, save_name=None, aggregation_period="hourly", aggregation_type="raw"):
    """
    Fetch data from the Aurassure API for specified sensors and aggregation period.
    Parameters:
        sensors (list): List of sensor IDs to fetch data for. Default is all sensors.
        aggregation_period (str): Aggregation period, either "hourly", "minutes" or "daily". Default is "hourly".
        aggregation_type (str): Type of aggregation, either "raw" or "aggregate". Default is "raw".
        start_time (datetime): Start time for data fetching. Default is 2 days ago.
        end_time (datetime): End time for data fetching. Default is current time.
    Returns:
        pandas.DataFrame: DataFrame containing the fetched data.
    """

    
    
    if sensors == all:
        sensors = [23883, 23884, 23885]
    else:
        sensors = sensors

    headers = {
        "Access-Id": AccessId,
        "Access-Key": AccessKey,
        "Content-Type": "application/json"
    }

    if end_time == None:
        end_time = datetime.now().replace(microsecond=0).timestamp()
        
    else:
        end_time = end_time.replace(microsecond=0).timestamp()

    if start_time == None:
        start_time = datetime.now() - timedelta(days=2)
        start_time.replace(microsecond=0)
        start_time = start_time.timestamp()
    else:
        start_time = start_time.replace(microsecond=0).timestamp()
        
    # start_time = end_time - timedelta(days=7)
    if save_to != None and save_name is None:
        save_name = f'aurassure_data_{str(datetime.fromtimestamp(start_time).replace(microsecond=0)).strip().replace(":", "-").replace(" ", "_")}_{str(datetime.fromtimestamp(end_time)).strip().replace(":", "-").replace(" ", "_")}.{save_to}'

    params = {
    "data_type": "raw",
    "aggregation_period": 0,
    "parameters": ["temp", "humid", "pm1", "pm2.5", "no2", "o3", "co"],
    "parameter_attributes": [],
    "things": sensors,
    "from_time": int(start_time),
    "upto_time": int(end_time),
    "data_source": ["processed", "callibrated"]
    }

    response = requests.post(f"{api_url}/clients/17067/applications/16/things/data", headers=headers, json=params)
    if response.status_code == 200:
        data = response.json()
        data = pd.json_normalize(data['data'], sep='_')
        data['time'] = pd.to_datetime(data['time'], unit='s')
        if save_to == 'csv':
            data.to_csv(f'{save_name}')
            print(f"Data saved to CSV file at {save_name}.")
        elif save_to == 'json':
            data.to_json(f'{save_name}', orient='records', lines=True)
            print(f"Data saved to JSON file at {save_name}.")
        else:
            pass
        return data
        
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    

print(get_data(save_to='csv'))