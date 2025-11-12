from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import os
import io
from aurasure import get_data

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Aurassure API is running"})

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

if __name__ == '__main__':
    # Use PORT environment variable for Google Cloud, default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('DEBUG', 'False') == 'True', host='0.0.0.0', port=port)
