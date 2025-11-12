"""
Main entry point for App Engine deployment.
This imports the Flask app from the backend directory.
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the Flask app
from app import app

if __name__ == '__main__':
    # This is used when running locally only. When deploying to App Engine,
    # a webserver process such as Gunicorn will serve the app.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
