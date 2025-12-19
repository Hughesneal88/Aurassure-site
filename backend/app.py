from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import os
import io
import re
from aurasure import get_data
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

# Enable CORS for all routes
# In production, you should configure allowed origins for security
# For GitHub Pages + Render, set CORS_ORIGINS environment variable
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    CORS(app)
else:
    # Parse comma-separated origins
    origins = [origin.strip() for origin in cors_origins.split(',')]
    CORS(app, origins=origins)

# Initialize background scheduler for Nebo data collection
scheduler = BackgroundScheduler()

# Import Nebo data collection function from nebo_script
try:
    from nebo_script import collect_nebo_data
    from nebo_data_manager import (
        get_nebo_sensors,
        download_nebo_data_from_drive
    )
    
    # Schedule the Nebo data collection to run every 2 minutes
    scheduler.add_job(func=collect_nebo_data, trigger="interval", minutes=2)
    scheduler.start()
    print("Nebo data collection scheduler started (runs every 2 minutes)")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    
    NEBO_ENABLED = True
except Exception as e:
    print(f"Warning: Nebo integration not available: {e}")
    NEBO_ENABLED = False

# Import Crafted Climate data functions
try:
    from crafted_climate_manager import (
        get_crafted_climate_sensors,
        download_crafted_climate_data,
        CRAFTED_CLIMATE_ENABLED
    )
    
    if CRAFTED_CLIMATE_ENABLED:
        print("Crafted Climate integration enabled")
    else:
        print("Warning: Crafted Climate integration not available - API key or AUID not configured")
except Exception as e:
    print(f"Warning: Crafted Climate integration not available: {e}")
    CRAFTED_CLIMATE_ENABLED = False

# Import AirVisual data functions
try:
    from airvisual_manager import (
        get_airvisual_sensors,
        download_airvisual_data,
        AIRVISUAL_ENABLED
    )
    
    if AIRVISUAL_ENABLED:
        print("AirVisual integration enabled")
except Exception as e:
    print(f"Warning: AirVisual integration not available: {e}")
    AIRVISUAL_ENABLED = False

# Import AirGradient data functions
try:
    from airgradient_manager import (
        get_airgradient_sensors,
        download_airgradient_data,
        AIRGRADIENT_ENABLED
    )
    
    if AIRGRADIENT_ENABLED:
        print("AirGradient integration enabled")
    else:
        print("Warning: AirGradient integration not available - API token not configured")
except Exception as e:
    print(f"Warning: AirGradient integration not available: {e}")
    AIRGRADIENT_ENABLED = False

# Import Envira data functions
try:
    from envira_manager import (
        get_envira_sensors,
        download_envira_data,
        ENVIRA_ENABLED
    )
    
    if ENVIRA_ENABLED:
        print("Envira integration enabled")
except Exception as e:
    print(f"Warning: Envira integration not available: {e}")
    ENVIRA_ENABLED = False

def sanitize_filename(filename):
    """Sanitize filename to prevent path injection"""
    # Remove any directory path components
    filename = os.path.basename(filename)
    # Replace any potentially dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Ensure filename doesn't start with a dot
    if filename.startswith('.'):
        filename = '_' + filename
    return filename

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Aurassure API is running",
        "nebo_enabled": NEBO_ENABLED,
        "crafted_climate_enabled": CRAFTED_CLIMATE_ENABLED,
        "airvisual_enabled": AIRVISUAL_ENABLED,
        "airgradient_enabled": AIRGRADIENT_ENABLED,
        "envira_enabled": ENVIRA_ENABLED
    })

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    """Get available sensors"""
    return jsonify({
        "sensors": [
            {"id": 23883, "name": "Sensor 1"},
            {"id": 23884, "name": "Sensor 2"},
            {"id": 23885, "name": "Sensor 3"}
        ]
    })

@app.route('/api/download', methods=['POST'])
def download_data():
    """
    Download data endpoint
    Expects JSON body with:
    - sensors: list of sensor IDs (optional, defaults to all)
    - start_time: ISO format datetime string (optional)
    - end_time: ISO format datetime string (optional)
    - format: 'csv' or 'json' (required)
    """
    try:
        data = request.get_json()
        
        # Parse parameters
        sensors = data.get('sensors', 'all')
        if sensors != 'all' and isinstance(sensors, list):
            sensors = [int(s) for s in sensors]
        
        format_type = data.get('format', 'csv')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Create a temporary filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"aurassure_data_{timestamp}.{format_type}"
        
        # Get data
        df = get_data(
            sensors=sensors if sensors != 'all' else all,
            start_time=start_time,
            end_time=end_time,
            save_to=format_type,
            save_name=temp_filename
        )
        
        if df is None:
            return jsonify({"error": "Failed to fetch data from Aurassure API"}), 500
        
        # Send file
        if os.path.exists(temp_filename):
            response = send_file(
                temp_filename,
                as_attachment=True,
                download_name=temp_filename,
                mimetype='application/octet-stream'
            )
            
            # Clean up file after sending
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                except Exception as e:
                    print(f"Error cleaning up file: {e}")
            
            return response
        else:
            return jsonify({"error": "File generation failed"}), 500
            
    except Exception as e:
        print(f"Error in download_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/preview', methods=['POST'])
def preview_data():
    """
    Preview data endpoint - returns first 10 rows as JSON
    Expects same parameters as download endpoint
    """
    try:
        data = request.get_json()
        
        # Parse parameters
        sensors = data.get('sensors', 'all')
        if sensors != 'all' and isinstance(sensors, list):
            sensors = [int(s) for s in sensors]
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data without saving
        df = get_data(
            sensors=sensors if sensors != 'all' else all,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None:
            return jsonify({"error": "Failed to fetch data from Aurassure API"}), 500
        
        # Return preview (first 10 rows)
        preview = df.head(10).to_dict(orient='records')
        
        # Convert timestamps to strings for JSON serialization
        for row in preview:
            if 'time' in row:
                row['time'] = str(row['time'])
        
        return jsonify({
            "preview": preview,
            "total_rows": len(df),
            "columns": list(df.columns)
        })
            
    except Exception as e:
        print(f"Error in preview_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/nebo/sensors', methods=['GET'])
def get_nebo_sensors_endpoint():
    """Get available Nebo sensors"""
    if not NEBO_ENABLED:
        return jsonify({"error": "Nebo integration not available"}), 503
    
    try:
        sensors = get_nebo_sensors()
        return jsonify({"sensors": sensors})
    except Exception as e:
        print(f"Error in get_nebo_sensors: {str(e)}")
        return jsonify({"error": "Failed to retrieve Nebo sensors"}), 500

@app.route('/api/nebo/download', methods=['POST'])
def download_nebo_data():
    """
    Download Nebo data from Google Drive
    Expects JSON body with:
    - sensors: list of sensor slugs (optional, defaults to all)
    - start_time: ISO format datetime string (optional)
    - end_time: ISO format datetime string (optional)
    - format: 'csv' or 'json' (required)
    """
    if not NEBO_ENABLED:
        return jsonify({"error": "Nebo integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_slugs = data.get('sensors', 'all')
        format_type = data.get('format', 'csv')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from Google Drive
        df = download_nebo_data_from_drive(
            sensor_slugs=sensor_slugs if sensor_slugs != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Create a temporary filename with safe directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = sanitize_filename(f"nebo_data_{timestamp}.{format_type}")
        # Use absolute path in a safe temporary directory
        temp_dir = os.path.abspath('/tmp')
        temp_filepath = os.path.join(temp_dir, safe_filename)
        
        # Save data to file
        if format_type == 'csv':
            df.to_csv(temp_filepath, index=False)
        elif format_type == 'json':
            df.to_json(temp_filepath, orient='records', lines=True)
        else:
            return jsonify({"error": "Invalid format. Use 'csv' or 'json'"}), 400
        
        # Send file
        if os.path.exists(temp_filepath):
            response = send_file(
                temp_filepath,
                as_attachment=True,
                download_name=safe_filename,
                mimetype='application/octet-stream'
            )
            
            # Clean up file after sending
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                except Exception as e:
                    print(f"Error cleaning up file: {e}")
            
            return response
        else:
            return jsonify({"error": "File generation failed"}), 500
            
    except Exception as e:
        print(f"Error in download_nebo_data: {str(e)}")
        return jsonify({"error": "Failed to download Nebo data"}), 500

@app.route('/api/nebo/preview', methods=['POST'])
def preview_nebo_data():
    """
    Preview Nebo data from Google Drive - returns first 10 rows as JSON
    Expects same parameters as download endpoint
    """
    if not NEBO_ENABLED:
        return jsonify({"error": "Nebo integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_slugs = data.get('sensors', 'all')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from Google Drive
        df = download_nebo_data_from_drive(
            sensor_slugs=sensor_slugs if sensor_slugs != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Return preview (first 10 rows)
        preview = df.head(10).to_dict(orient='records')
        
        # Convert timestamps to strings for JSON serialization
        for row in preview:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = str(value)
        
        return jsonify({
            "preview": preview,
            "total_rows": len(df),
            "columns": list(df.columns)
        })
            
    except Exception as e:
        print(f"Error in preview_nebo_data: {str(e)}")
        return jsonify({"error": "Failed to preview Nebo data"}), 500

@app.route('/api/crafted-climate/sensors', methods=['GET'])
def get_crafted_climate_sensors_endpoint():
    """Get available Crafted Climate sensors"""
    if not CRAFTED_CLIMATE_ENABLED:
        return jsonify({"error": "Crafted Climate integration not available"}), 503
    
    try:
        sensors = get_crafted_climate_sensors()
        return jsonify({"sensors": sensors})
    except Exception as e:
        print(f"Error in get_crafted_climate_sensors: {str(e)}")
        return jsonify({"error": "Failed to retrieve Crafted Climate sensors"}), 500

@app.route('/api/crafted-climate/download', methods=['POST'])
def download_crafted_climate_data_endpoint():
    """
    Download Crafted Climate data
    Expects JSON body with:
    - sensors: list of sensor IDs (AUIDs) (optional, defaults to all)
    - start_time: ISO format datetime string (optional)
    - end_time: ISO format datetime string (optional)
    - format: 'csv' or 'json' (required)
    """
    if not CRAFTED_CLIMATE_ENABLED:
        return jsonify({"error": "Crafted Climate integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_ids = data.get('sensors', 'all')
        format_type = data.get('format', 'csv')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from Crafted Climate API
        df = download_crafted_climate_data(
            sensor_ids=sensor_ids if sensor_ids != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Create a temporary filename with safe directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = sanitize_filename(f"crafted_climate_data_{timestamp}.{format_type}")
        # Use absolute path in a safe temporary directory
        temp_dir = os.path.abspath('/tmp')
        temp_filepath = os.path.join(temp_dir, safe_filename)
        
        # Save data to file
        if format_type == 'csv':
            df.to_csv(temp_filepath, index=False)
        elif format_type == 'json':
            df.to_json(temp_filepath, orient='records', lines=True)
        else:
            return jsonify({"error": "Invalid format. Use 'csv' or 'json'"}), 400
        
        # Send file
        if os.path.exists(temp_filepath):
            response = send_file(
                temp_filepath,
                as_attachment=True,
                download_name=safe_filename,
                mimetype='application/octet-stream'
            )
            
            # Clean up file after sending
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                except Exception as e:
                    print(f"Error cleaning up file: {e}")
            
            return response
        else:
            return jsonify({"error": "File generation failed"}), 500
            
    except Exception as e:
        print(f"Error in download_crafted_climate_data: {str(e)}")
        return jsonify({"error": "Failed to download Crafted Climate data"}), 500

@app.route('/api/crafted-climate/preview', methods=['POST'])
def preview_crafted_climate_data():
    """
    Preview Crafted Climate data - returns first 10 rows as JSON
    Expects same parameters as download endpoint
    """
    if not CRAFTED_CLIMATE_ENABLED:
        return jsonify({"error": "Crafted Climate integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_ids = data.get('sensors', 'all')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from Crafted Climate API
        df = download_crafted_climate_data(
            sensor_ids=sensor_ids if sensor_ids != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Return preview (first 10 rows)
        preview = df.head(10).to_dict(orient='records')
        
        # Convert timestamps to strings for JSON serialization
        for row in preview:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = str(value)
        
        return jsonify({
            "preview": preview,
            "total_rows": len(df),
            "columns": list(df.columns)
        })
            
    except Exception as e:
        print(f"Error in preview_crafted_climate_data: {str(e)}")
        return jsonify({"error": "Failed to preview Crafted Climate data"}), 500

# ==================== AirVisual Endpoints ====================

@app.route('/api/airvisual/sensors', methods=['GET'])
def get_airvisual_sensors_endpoint():
    """Get available AirVisual sensors"""
    if not AIRVISUAL_ENABLED:
        return jsonify({"error": "AirVisual integration not available"}), 503
    
    try:
        sensors = get_airvisual_sensors()
        return jsonify({"sensors": sensors})
    except Exception as e:
        print(f"Error in get_airvisual_sensors: {str(e)}")
        return jsonify({"error": "Failed to retrieve AirVisual sensors"}), 500

@app.route('/api/airvisual/download', methods=['POST'])
def download_airvisual_data_endpoint():
    """
    Download AirVisual data
    Expects JSON body with:
    - sensors: list of sensor IDs (device IDs) (optional, defaults to all)
    - start_time: ISO format datetime string (optional)
    - end_time: ISO format datetime string (optional)
    - format: 'csv' or 'json' (required)
    """
    if not AIRVISUAL_ENABLED:
        return jsonify({"error": "AirVisual integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_ids = data.get('sensors', 'all')
        format_type = data.get('format', 'csv')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from AirVisual API
        df = download_airvisual_data(
            sensor_ids=sensor_ids if sensor_ids != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Create a temporary filename with safe directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = sanitize_filename(f"airvisual_data_{timestamp}.{format_type}")
        # Use absolute path in a safe temporary directory
        temp_dir = os.path.abspath('/tmp')
        temp_filepath = os.path.join(temp_dir, safe_filename)
        
        # Save data to file
        if format_type == 'csv':
            df.to_csv(temp_filepath, index=False)
        elif format_type == 'json':
            df.to_json(temp_filepath, orient='records', lines=True)
        else:
            return jsonify({"error": "Invalid format. Use 'csv' or 'json'"}), 400
        
        # Send file
        if os.path.exists(temp_filepath):
            response = send_file(
                temp_filepath,
                as_attachment=True,
                download_name=safe_filename,
                mimetype='application/octet-stream'
            )
            
            # Clean up file after sending
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                except Exception as e:
                    print(f"Error cleaning up file: {e}")
            
            return response
        else:
            return jsonify({"error": "File generation failed"}), 500
            
    except Exception as e:
        print(f"Error in download_airvisual_data: {str(e)}")
        return jsonify({"error": "Failed to download AirVisual data"}), 500

@app.route('/api/airvisual/preview', methods=['POST'])
def preview_airvisual_data():
    """
    Preview AirVisual data - returns first 10 rows as JSON
    Expects same parameters as download endpoint
    """
    if not AIRVISUAL_ENABLED:
        return jsonify({"error": "AirVisual integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_ids = data.get('sensors', 'all')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from AirVisual API
        df = download_airvisual_data(
            sensor_ids=sensor_ids if sensor_ids != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Return preview (first 10 rows)
        preview = df.head(10).to_dict(orient='records')
        
        # Convert timestamps to strings for JSON serialization
        for row in preview:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = str(value)
        
        return jsonify({
            "preview": preview,
            "total_rows": len(df),
            "columns": list(df.columns)
        })
            
    except Exception as e:
        print(f"Error in preview_airvisual_data: {str(e)}")
        return jsonify({"error": "Failed to preview AirVisual data"}), 500

# ==================== AirGradient Endpoints ====================

@app.route('/api/airgradient/sensors', methods=['GET'])
def get_airgradient_sensors_endpoint():
    """Get available AirGradient sensors"""
    if not AIRGRADIENT_ENABLED:
        return jsonify({"error": "AirGradient integration not available"}), 503
    
    try:
        sensors = get_airgradient_sensors()
        return jsonify({"sensors": sensors})
    except Exception as e:
        print(f"Error in get_airgradient_sensors: {str(e)}")
        return jsonify({"error": "Failed to retrieve AirGradient sensors"}), 500

@app.route('/api/airgradient/download', methods=['POST'])
def download_airgradient_data_endpoint():
    """
    Download AirGradient data
    Expects JSON body with:
    - sensors: list of sensor IDs (optional, defaults to all)
    - start_time: ISO format datetime string (optional)
    - end_time: ISO format datetime string (optional)
    - format: 'csv' or 'json' (required)
    """
    if not AIRGRADIENT_ENABLED:
        return jsonify({"error": "AirGradient integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_ids = data.get('sensors', 'all')
        format_type = data.get('format', 'csv')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from AirGradient API
        df = download_airgradient_data(
            sensor_ids=sensor_ids if sensor_ids != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Create a temporary filename with safe directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = sanitize_filename(f"airgradient_data_{timestamp}.{format_type}")
        # Use absolute path in a safe temporary directory
        temp_dir = os.path.abspath('/tmp')
        temp_filepath = os.path.join(temp_dir, safe_filename)
        
        # Save data to file
        if format_type == 'csv':
            df.to_csv(temp_filepath, index=False)
        elif format_type == 'json':
            df.to_json(temp_filepath, orient='records', lines=True)
        else:
            return jsonify({"error": "Invalid format. Use 'csv' or 'json'"}), 400
        
        # Send file
        if os.path.exists(temp_filepath):
            response = send_file(
                temp_filepath,
                as_attachment=True,
                download_name=safe_filename,
                mimetype='application/octet-stream'
            )
            
            # Clean up file after sending
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                except Exception as e:
                    print(f"Error cleaning up file: {e}")
            
            return response
        else:
            return jsonify({"error": "File generation failed"}), 500
            
    except Exception as e:
        print(f"Error in download_airgradient_data: {str(e)}")
        return jsonify({"error": "Failed to download AirGradient data"}), 500

@app.route('/api/airgradient/preview', methods=['POST'])
def preview_airgradient_data():
    """
    Preview AirGradient data - returns first 10 rows as JSON
    Expects same parameters as download endpoint
    """
    if not AIRGRADIENT_ENABLED:
        return jsonify({"error": "AirGradient integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_ids = data.get('sensors', 'all')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from AirGradient API
        df = download_airgradient_data(
            sensor_ids=sensor_ids if sensor_ids != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Return preview (first 10 rows)
        preview = df.head(10).to_dict(orient='records')
        
        # Convert timestamps to strings for JSON serialization
        for row in preview:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = str(value)
        
        return jsonify({
            "preview": preview,
            "total_rows": len(df),
            "columns": list(df.columns)
        })
            
    except Exception as e:
        print(f"Error in preview_airgradient_data: {str(e)}")
        return jsonify({"error": "Failed to preview AirGradient data"}), 500

# ==================== Envira Endpoints ====================

@app.route('/api/envira/sensors', methods=['GET'])
def get_envira_sensors_endpoint():
    """Get available Envira sensors"""
    if not ENVIRA_ENABLED:
        return jsonify({"error": "Envira integration not available"}), 503
    
    try:
        sensors = get_envira_sensors()
        return jsonify({"sensors": sensors})
    except Exception as e:
        print(f"Error in get_envira_sensors: {str(e)}")
        return jsonify({"error": "Failed to retrieve Envira sensors"}), 500

@app.route('/api/envira/download', methods=['POST'])
def download_envira_data_endpoint():
    """
    Download Envira data
    Expects JSON body with:
    - sensors: list of sensor UUIDs (optional, defaults to all)
    - start_time: ISO format datetime string (optional)
    - end_time: ISO format datetime string (optional)
    - format: 'csv' or 'json' (required)
    """
    if not ENVIRA_ENABLED:
        return jsonify({"error": "Envira integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_ids = data.get('sensors', 'all')
        format_type = data.get('format', 'csv')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from Envira API
        df = download_envira_data(
            sensor_ids=sensor_ids if sensor_ids != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Create a temporary filename with safe directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = sanitize_filename(f"envira_data_{timestamp}.{format_type}")
        # Use absolute path in a safe temporary directory
        temp_dir = os.path.abspath('/tmp')
        temp_filepath = os.path.join(temp_dir, safe_filename)
        
        # Save data to file
        if format_type == 'csv':
            df.to_csv(temp_filepath, index=False)
        elif format_type == 'json':
            df.to_json(temp_filepath, orient='records', lines=True)
        else:
            return jsonify({"error": "Invalid format. Use 'csv' or 'json'"}), 400
        
        # Send file
        if os.path.exists(temp_filepath):
            response = send_file(
                temp_filepath,
                as_attachment=True,
                download_name=safe_filename,
                mimetype='application/octet-stream'
            )
            
            # Clean up file after sending
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                except Exception as e:
                    print(f"Error cleaning up file: {e}")
            
            return response
        else:
            return jsonify({"error": "File generation failed"}), 500
            
    except Exception as e:
        print(f"Error in download_envira_data: {str(e)}")
        return jsonify({"error": "Failed to download Envira data"}), 500

@app.route('/api/envira/preview', methods=['POST'])
def preview_envira_data():
    """
    Preview Envira data - returns first 10 rows as JSON
    Expects same parameters as download endpoint
    """
    if not ENVIRA_ENABLED:
        return jsonify({"error": "Envira integration not available"}), 503
    
    try:
        data = request.get_json()
        
        # Parse parameters
        sensor_ids = data.get('sensors', 'all')
        
        # Parse datetime strings if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # Get data from Envira API
        df = download_envira_data(
            sensor_ids=sensor_ids if sensor_ids != 'all' else None,
            start_time=start_time,
            end_time=end_time
        )
        
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified parameters"}), 404
        
        # Return preview (first 10 rows)
        preview = df.head(10).to_dict(orient='records')
        
        # Convert timestamps to strings for JSON serialization
        for row in preview:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = str(value)
        
        return jsonify({
            "preview": preview,
            "total_rows": len(df),
            "columns": list(df.columns)
        })
            
    except Exception as e:
        print(f"Error in preview_envira_data: {str(e)}")
        return jsonify({"error": "Failed to preview Envira data"}), 500

if __name__ == '__main__':
    # Use PORT environment variable for Google Cloud, default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('DEBUG', 'False') == 'True', host='0.0.0.0', port=port)
