# Aurassure Data Download Site

A modern web application for downloading environmental sensor data from Aurassure, featuring a Flask backend and React frontend.

## Features

- 🎨 Modern, aesthetically pleasing UI with gradient design
- 📊 Preview data before downloading
- 📅 Flexible date/time range selection
- 🔧 Sensor selection (individual or all sensors)
- 💾 Multiple download formats (CSV, JSON)
- 🚀 Fast and responsive

## Architecture

- **Backend**: Flask (Python) - REST API for data retrieval
- **Frontend**: React - Modern, responsive user interface
- **Data Source**: Aurassure IoT Platform API

## Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- Aurassure API credentials (Access ID and Access Key)

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the root directory with your Aurassure credentials:

```env
AccessId=your_access_id_here
AccessKey=your_access_key_here
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
2. Select sensors (or choose "Select All Sensors")
3. Choose a date/time range (defaults to last 2 days)
4. Select your preferred download format (CSV or JSON)
5. Click "Preview Data" to see a sample of the data
6. Click "Download Data" to download the full dataset

## API Endpoints

### Backend API

- `GET /api/health` - Health check endpoint
- `GET /api/sensors` - Get list of available sensors
- `POST /api/download` - Download data
  - Body: `{ sensors, start_time, end_time, format }`
- `POST /api/preview` - Preview data (first 10 rows)
  - Body: `{ sensors, start_time, end_time }`

## Project Structure

```
Aurassure-site/
├── backend/
│   ├── app.py              # Flask application
│   ├── aurasure.py         # Data fetching logic
│   └── requirements.txt    # Python dependencies
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

- `AccessId` - Aurassure API Access ID (required)
- `AccessKey` - Aurassure API Access Key (required)
- `REACT_APP_API_URL` - Backend API URL (default: http://localhost:5000)
- `PORT` - Server port (default: 5000 for local, 8080 for GCP)

## Deployment to Google Cloud Platform

This application is ready to deploy to Google Cloud Platform. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### Quick Deploy to App Engine

```bash
# Build the frontend
cd frontend && npm run build && cd ..

# Deploy to App Engine
gcloud app deploy
```

### Quick Deploy to Cloud Run

```bash
# Build and deploy with one command
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aurassure-app
gcloud run deploy aurassure-app --image gcr.io/YOUR_PROJECT_ID/aurassure-app
```

### Using the Deployment Script

```bash
./deploy.sh
```

The deployment script provides an interactive menu to:
- Deploy to App Engine
- Deploy to Cloud Run
- Build frontend only

For complete deployment instructions, environment variable setup, and troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md).

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
