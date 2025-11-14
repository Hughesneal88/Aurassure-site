# Aurassure Data Download Site

A modern web application for downloading environmental sensor data from Aurassure, featuring a Flask backend and React frontend.

## 🚀 Quick Start

**Want to deploy right away?** Choose your platform:

- **[GitHub Pages + Render (Free)](QUICKSTART_GITHUB_RENDER.md)** - Free hosting, simple setup
- **[Google Cloud Platform](QUICKSTART_GCP.md)** - Enterprise-grade, scalable

**Running locally?** See [Local Development](#local-development) below.

## Features

- 🎨 Modern, aesthetically pleasing UI with gradient design
- 📊 Preview data before downloading
- 📅 Flexible date/time range selection
- 🔧 Sensor selection (individual or all sensors)
- 💾 Multiple download formats (CSV, JSON)
- 🚀 Fast and responsive
- 🔄 **NEW**: Nebo sensor data integration with automatic 2-minute collection cycle
- ☁️ **NEW**: Google Drive storage for Nebo sensor data
- 📈 **NEW**: Download Nebo data within custom time ranges
- 🌡️ **NEW**: Crafted Climate sensor data integration

## Architecture

- **Backend**: Flask (Python) - REST API for data retrieval
- **Frontend**: React - Modern, responsive user interface
- **Data Sources**: 
  - Aurassure IoT Platform API (real-time API access)
  - Nebo Sensors API (periodic collection, Google Drive storage)
  - Crafted Climate API (on-demand data retrieval)
- **Storage**: Google Drive integration for Nebo sensor data
- **Scheduler**: Background job scheduler for automatic Nebo data collection every 2 minutes

## Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- Aurassure API credentials (Access ID and Access Key)
- **(Optional)** Google Drive service account credentials for Nebo integration
- **(Optional)** Crafted Climate API credentials for Crafted Climate integration

## Local Development

Run the application on your local machine for development and testing.

### 1. Environment Variables

Create a `.env` file in the root directory with your Aurassure credentials:

```env
AccessId=your_access_id_here
AccessKey=your_access_key_here

# Optional: Crafted Climate API credentials
CRAFTED_CLIMATE_API_KEY=your_crafted_climate_api_key_here
CRAFTED_CLIMATE_AUID=your_crafted_climate_auid_here
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run the Flask server
python app.py
```

The backend will start on `http://localhost:5000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will start on `http://localhost:3000`

### 4. Quick Start with Startup Scripts

For convenience, you can use the provided startup scripts to run both servers simultaneously:

**On Linux/macOS (Bash):**
```bash
./start.sh
```

**On Windows (PowerShell):**
```powershell
.\start.ps1
```

These scripts will:
- Check for the `.env` file
- Start both the backend and frontend servers
- Display the server URLs
- Allow you to stop both servers with Ctrl+C

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Select the data source (Aurassure, Nebo, or Crafted Climate)
3. Select sensors (or choose "Select All Sensors")
4. Choose a date/time range (defaults to last 2 days)
5. Select your preferred download format (CSV or JSON)
6. Click "Preview Data" to see a sample of the data
7. Click "Download Data" to download the full dataset

## API Endpoints

### Aurassure Endpoints

- `GET /api/health` - Health check endpoint (includes Nebo and Crafted Climate availability status)
- `GET /api/sensors` - Get list of available Aurassure sensors
- `POST /api/download` - Download Aurassure data
  - Body: `{ sensors, start_time, end_time, format }`
- `POST /api/preview` - Preview Aurassure data (first 10 rows)
  - Body: `{ sensors, start_time, end_time }`

### Nebo Endpoints

- `GET /api/nebo/sensors` - Get list of available Nebo sensors
- `POST /api/nebo/download` - Download Nebo data from Google Drive
  - Body: `{ sensors, start_time, end_time, format }`
  - Note: Downloads data that has been collected and stored in Google Drive
- `POST /api/nebo/preview` - Preview Nebo data (first 10 rows)
  - Body: `{ sensors, start_time, end_time }`

### Crafted Climate Endpoints

- `GET /api/crafted-climate/sensors` - Get list of available Crafted Climate sensors
- `POST /api/crafted-climate/download` - Download Crafted Climate data
  - Body: `{ sensors, start_time, end_time, format }`
  - Note: Fetches data directly from Crafted Climate API on-demand
- `POST /api/crafted-climate/preview` - Preview Crafted Climate data (first 10 rows)
  - Body: `{ sensors, start_time, end_time }`

## Project Structure

```
Aurassure-site/
├── backend/
│   ├── app.py                     # Flask application with API endpoints and scheduler
│   ├── aurasure.py                # Aurassure data fetching logic
│   ├── nebo_data_manager.py       # Nebo data retrieval functions
│   ├── nebo_script.py             # Nebo data collection script (used by scheduler)
│   ├── crafted_climate.py         # Crafted Climate API integration
│   ├── crafted_climate_manager.py # Crafted Climate data retrieval functions
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── App.css        # Styling
│   │   └── index.js       # Entry point
│   └── package.json       # Node dependencies
├── .env                   # Environment variables (create this)
├── start.sh               # Startup script for Linux/macOS
├── start.ps1              # Startup script for Windows
└── README.md
```

## Development

### Running in Development Mode

Both servers support hot reloading:

- Backend: Flask debug mode is enabled by default
- Frontend: React development server watches for changes

### Building for Production

#### Frontend

```bash
cd frontend
npm run build
```

This creates an optimized production build in `frontend/build/`.

## Environment Variables

- `AccessId` - Aurassure API Access ID (required for Aurassure data)
- `AccessKey` - Aurassure API Access Key (required for Aurassure data)
- `REACT_APP_API_URL` - Backend API URL (default: http://localhost:5000)
- `PORT` - Server port (default: 5000 for local, 8080 for GCP, 10000 for Render)
- `CORS_ORIGINS` - Allowed CORS origins (default: *, set to specific URLs in production)

### Crafted Climate Integration (Optional)

To enable Crafted Climate sensor data:

1. Add the following environment variables to your `.env` file:
   - `CRAFTED_CLIMATE_API_KEY` - Your Crafted Climate API key
   - `CRAFTED_CLIMATE_AUID` - Your Crafted Climate sensor AUID (e.g., AU-001-CC1N-01)
2. The Crafted Climate integration will automatically activate when both credentials are set
3. The Crafted Climate data source option will appear in the frontend UI when available
4. Data is fetched on-demand when you preview or download

**Note**: If credentials are not configured, the application will run normally with only Aurassure and Nebo data available.

### Nebo Integration (Optional)

To enable Nebo sensor data collection and storage:

1. Place a `service_account.json` file in the `backend/` directory with Google Drive service account credentials
2. **Configure the Google Drive folder**:
   - The `GOOGLE_DRIVE_FOLDER_ID` in `backend/nebo_script.py` must point to a folder in a **Shared Drive** (Team Drive)
   - Service accounts do not have storage quota for regular folders - they can only write to Shared Drives
   - Get the folder ID from the URL: `https://drive.google.com/drive/folders/YOUR_FOLDER_ID`
   - Ensure the service account has write access to the Shared Drive
3. The Nebo integration will automatically activate when the service account file is present
4. **Data is automatically collected every 2 minutes** by the Flask app's background scheduler (APScheduler) which runs the `collect_nebo_data()` function from `nebo_script.py`
5. The Nebo data source option will appear in the frontend UI when available

**Important**: 
- If you encounter a "Service Accounts do not have storage quota" error, verify that your folder is in a Shared Drive, not a regular folder. See [Google's Shared Drives documentation](https://developers.google.com/workspace/drive/api/guides/about-shareddrives) for more information.
- The `nebo_script.py` can also be run standalone for testing or manual data collection.

**Note**: If the service account file is not present, the application will run normally with only Aurassure data available.

## Deployment Options

This application supports multiple deployment platforms:

### Option 1: GitHub Pages + Render (Recommended for Free Hosting) 🆓

Deploy the frontend to GitHub Pages and backend to Render for a free, scalable solution.

**Quick Start:**
1. Deploy backend to [Render](https://render.com)
2. Set `REACT_APP_API_URL` repository variable in GitHub
3. Push to `main` branch - GitHub Actions automatically deploys frontend

**Benefits:**
- ✅ Free hosting for both frontend and backend
- ✅ Automatic deployments on push
- ✅ HTTPS enabled by default
- ✅ Perfect for public-facing applications

📖 **Full Guide:** [DEPLOYMENT_GITHUB_RENDER.md](DEPLOYMENT_GITHUB_RENDER.md) | [Quick Start](QUICKSTART_GITHUB_RENDER.md)

### Option 2: Google Cloud Platform ☁️

Deploy to Google App Engine or Cloud Run for enterprise-grade infrastructure.

**Quick Deploy:**
```bash
# Build the frontend
cd frontend && npm run build && cd ..

# Deploy to App Engine
gcloud app deploy
```

**Benefits:**
- ✅ Enterprise-grade infrastructure
- ✅ Advanced scaling and monitoring
- ✅ Integration with other GCP services
- ✅ 99.95% SLA on paid tier

📖 **Full Guide:** [DEPLOYMENT.md](DEPLOYMENT.md) | [Quick Start](QUICKSTART_GCP.md)

### Comparison

| Feature | GitHub Pages + Render | Google Cloud Platform |
|---------|----------------------|----------------------|
| **Free Tier** | ✅ Generous | ⚠️ Limited |
| **Setup Complexity** | Easy | Moderate |
| **Best For** | Personal/Small Projects | Enterprise/Large Scale |

## Security Notes

- Never commit your `.env` file to version control
- Keep your API credentials secure
- Use HTTPS in production
- Consider implementing rate limiting for production use

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure:
- Flask-CORS is installed: `pip install flask-cors`
- The backend is running on port 5000
- The frontend is configured to use the correct API URL

### Missing Dependencies

If modules are not found:
- Backend: `pip install -r backend/requirements.txt`
- Frontend: `cd frontend && npm install`

## License

This project is for internal use with Aurassure data.

## Support

For issues or questions, please contact your system administrator.
