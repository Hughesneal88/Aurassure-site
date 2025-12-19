import requests
import json
import datetime

# Device API endpoints
DEVICES = {
    "NUXK": "https://device.iqair.com/v2/686d464aad899b2bc5156788",
    "5UEO": "https://device.iqair.com/v2/686d479c83f5802962f3d379",
    "215J": "https://device.iqair.com/v2/688768ce8863f9662b51a598"
}

def get_device_rec(device_id="NUXK"):
    """
    Fetch device data from IQAir API
    
    Args:
        device_id: Device identifier (NUXK, 5UEO, or 215J)
    
    Returns:
        Tuple containing:
        obj[0] = city
        obj[1] = country
        obj[2] = aqius
        obj[3] = weather
        obj[4] = passed_time
        obj[5] = w_icon (weather Icon)
        obj[6] = humidity
        obj[7] = pm25conc
    """
    if device_id not in DEVICES:
        raise ValueError(f"Invalid device_id: {device_id}. Must be one of {list(DEVICES.keys())}")
    
    response = requests.get(DEVICES[device_id])
    obj = json.loads(json.dumps(response.json()))
    city = "Accra"
    country = "Ghana"
    if 'code' in obj:
        with open("data.json", "r") as f:
            obj = json.load(f)
            aqius = obj['historical']['instant'][0]['pm25']['aqius'] #AQI US
            pm25conc = obj['historical']['instant'][0]['pm25']['conc']
            weather = obj['historical']['instant'][0]['tp']
            w_icon = 0
            humidity = obj['historical']['instant'][0]['hm']
            passed_time = obj['historical']['instant'][0]['ts']
            passed_time = datetime.datetime.strptime(passed_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            passed_time = passed_time.strftime("%A, %d. %B %Y %I:%M %p")
    else:
        with open("data.json", "w") as f:
            json.dump(obj, f)
        aqius = obj['historical']['instant'][0]['pm25']['aqius'] #AQI US
        pm25conc = obj['historical']['instant'][0]['pm25']['conc'] 
        weather = obj['historical']['instant'][0]['tp']
        w_icon = 0
        humidity = obj['historical']['instant'][0]['hm']
#     # given_time = obj['data']['current']['pollution']['ts']
#     # passed_time = round(time_elapsed(given_time).seconds/1000)
        passed_time = obj['historical']['instant'][0]['ts']
        passed_time = datetime.datetime.strptime(passed_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        passed_time = passed_time.strftime("%a, %d %B %Y %I:%M %p")
#     # aqicn = obj['data']['current']['pollution']['aqicn']   # AQI GLOBAL
    return city, country, aqius, passed_time, weather, w_icon, humidity, pm25conc


def get_all_historical_data(device_id="NUXK"):
    """
    Fetch and display all available historical data for a device
    
    Args:
        device_id: Device identifier (NUXK, 5UEO, or 215J)
    
    Returns:
        Dictionary containing all historical data from the API
    """
    if device_id not in DEVICES:
        raise ValueError(f"Invalid device_id: {device_id}. Must be one of {list(DEVICES.keys())}")
    
    response = requests.get(DEVICES[device_id])
    obj = json.loads(json.dumps(response.json()))
    
    # Check if we have valid data
    if 'code' in obj:
        print(f"Error fetching data for {device_id}: {obj.get('message', 'Unknown error')}")
        # Try to load from cache
        try:
            with open("data.json", "r") as f:
                obj = json.load(f)
        except FileNotFoundError:
            return None
    else:
        # Save to cache
        with open("data.json", "w") as f:
            json.dump(obj, f, indent=2)
    
    # Display all historical data
    if 'historical' in obj:
        print(f"\n=== Historical Data for Device {device_id} ===")
        print(json.dumps(obj['historical'], indent=2))
        return obj['historical']
    else:
        print(f"No historical data found for device {device_id}")
        return None


if __name__ == "__main__":
    print(get_all_historical_data())