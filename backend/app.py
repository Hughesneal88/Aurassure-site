from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import os
import io
import re
import requests
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

# Keep-alive function to prevent Render service from spinning down
def keep_alive():
    """Ping the Render service URL to keep it active"""
    render_url = os.environ.get('RENDER_SERVICE_URL', 'https://aurassure-site.onrender.com')
    try:
        requests.get(render_url, timeout=10)
        print(f"Keep-alive ping successful to {render_url}")
    except Exception as e:
        # Silently fail - we don't want to disrupt the service
        print(f"Keep-alive ping failed: {e}")

# Import Nebo data manager functions
try:
    from nebo_data_manager import (
        collect_nebo_data,
        get_nebo_sensors,
        download_nebo_data_from_drive
    )
    
    # Schedule the Nebo data collection to run every 2 minutes
    scheduler.add_job(func=collect_nebo_data, trigger="interval", minutes=2)
    print("Nebo data collection scheduler started (runs every 2 minutes)")
    
    NEBO_ENABLED = True
except Exception as e:
    print(f"Warning: Nebo integration not available: {e}")
    NEBO_ENABLED = False

# Schedule keep-alive ping every 30 seconds
scheduler.add_job(func=keep_alive, trigger="interval", seconds=30)
print("Keep-alive scheduler started (runs every 30 seconds)")

# Start the scheduler
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

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
        "nebo_enabled": NEBO_ENABLED
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

if __name__ == '__main__':
    # Use PORT environment variable for Google Cloud, default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('DEBUG', 'False') == 'True', host='0.0.0.0', port=port)
