import requests
import json
from datetime import datetime, timedelta
import time

BASE_URL = "https://airlab.enviraiot.es/api/device"

def get_device_data(device_uuid, start_timestamp=None, end_timestamp=None, sensor=None):
    """
    Fetch data from Envira IoT API for a specific device
    
    Args:
        device_uuid: The UUID of the device
        start_timestamp: Start timestamp (Unix timestamp or ISO format). 
                        Defaults to 24 hours ago if None.
        end_timestamp: End timestamp (Unix timestamp or ISO format). 
                      Defaults to now if None.
    
    Returns:
        Dictionary containing the device data or None if request fails
    """
    # Set default timestamps if not provided
    if end_timestamp is None:
        end_timestamp = int(time.time() * 1000)  # Current time in milliseconds
    elif isinstance(end_timestamp, str):
        # Convert ISO format to timestamp
        end_timestamp = int(datetime.fromisoformat(end_timestamp.replace('Z', '+00:00')).timestamp() * 1000)
    
    if start_timestamp is None:
        # Default to 24 hours ago
        start_timestamp = end_timestamp - (24 * 60 * 60 * 1000)
    elif isinstance(start_timestamp, str):
        # Convert ISO format to timestamp
        start_timestamp = int(datetime.fromisoformat(start_timestamp.replace('Z', '+00:00')).timestamp() * 1000)
    
    url = f"{BASE_URL}/{device_uuid}/data/pm2.5?range.from={start_timestamp}&range.to={end_timestamp}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Envira API: {e}")
        return None


def get_device_data_formatted(device_uuid, start_timestamp=None, end_timestamp=None):
    """
    Fetch data from Envira IoT API and return formatted information
    
    Args:
        device_uuid: The UUID of the device
        start_timestamp: Start timestamp (Unix timestamp or ISO format)
        end_timestamp: End timestamp (Unix timestamp or ISO format)
    
    Returns:
        Dictionary with formatted device data including measurements
    """
    data = get_device_data(device_uuid, start_timestamp, end_timestamp)
    
    if data is None:
        return None
    
    # Parse and format the response
    formatted_data = {
        "device_uuid": device_uuid,
        "fetched_at": datetime.now().isoformat(),
        "raw_data": data
    }
    
    # Extract measurements if available
    if isinstance(data, dict) and "data" in data:
        measurements = data.get("data", [])
        formatted_data["measurement_count"] = len(measurements)
        if measurements:
            formatted_data["latest_measurement"] = measurements[-1]
            formatted_data["measurements"] = measurements
    
    return formatted_data


def save_device_data(device_uuid, filename=None, start_timestamp=None, end_timestamp=None):
    """
    Fetch device data and save to JSON file
    
    Args:
        device_uuid: The UUID of the device
        filename: Output filename (defaults to device_uuid.json)
        start_timestamp: Start timestamp
        end_timestamp: End timestamp
    
    Returns:
        Path to saved file or None if failed
    """
    if filename is None:
        filename = f"{device_uuid}.json"
    
    data = get_device_data(device_uuid, start_timestamp, end_timestamp)
    
    if data is None:
        return None
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {filename}")
        return filename
    except IOError as e:
        print(f"Error saving data to file: {e}")
        return None


def display_device_data(device_uuid, start_timestamp=None, end_timestamp=None):
    """
    Fetch and display device data in a formatted way
    
    Args:
        device_uuid: The UUID of the device
        start_timestamp: Start timestamp
        end_timestamp: End timestamp
    """
    data = get_device_data_formatted(device_uuid, start_timestamp, end_timestamp)
    
    if data is None:
        print("Failed to fetch device data")
        return
    
    print(f"\n=== Device Data ===")
    print(f"Device UUID: {data['device_uuid']}")
    print(f"Fetched at: {data['fetched_at']}")
    print(f"Measurements count: {data.get('measurement_count', 'N/A')}")
    print(f"\nFull data:")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    end_timestamp = datetime.now()
    start_timestamp = end_timestamp - timedelta(days=1)

    display_device_data(
        "fba1d9dd-5031-334d-4e2e-3120ff0f3429",
        start_timestamp=start_timestamp.isoformat(),
        end_timestamp=end_timestamp.isoformat()
    )