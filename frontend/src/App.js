import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [dataSource, setDataSource] = useState('aurassure');
  const [sensors, setSensors] = useState([]);
  const [selectedSensors, setSelectedSensors] = useState([]);
  const [selectAll, setSelectAll] = useState(true);
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [format, setFormat] = useState('csv');
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [neboEnabled, setNeboEnabled] = useState(false);

  const formatDateTimeLocal = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const checkNeboStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/health`);
      setNeboEnabled(response.data.nebo_enabled || false);
    } catch (err) {
      console.error('Error checking Nebo status:', err);
      setNeboEnabled(false);
    }
  }, []);

  const fetchSensors = useCallback(async () => {
    try {
      const endpoint = dataSource === 'nebo' 
        ? `${API_BASE_URL}/api/nebo/sensors`
        : `${API_BASE_URL}/api/sensors`;
      
      const response = await axios.get(endpoint);
      setSensors(response.data.sensors);
    } catch (err) {
      console.error('Error fetching sensors:', err);
      setError('Failed to fetch sensors');
    }
  }, [dataSource]);

  useEffect(() => {
    // Check if Nebo is enabled
    checkNeboStatus();
    
    // Fetch available sensors
    fetchSensors();
    
    // Set default dates (last 2 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 2);
    
    setEndTime(formatDateTimeLocal(end));
    setStartTime(formatDateTimeLocal(start));
  }, [checkNeboStatus, fetchSensors]);

  // Re-fetch sensors when data source changes
  useEffect(() => {
    fetchSensors();
    setSelectedSensors([]);
    setSelectAll(true);
    setPreview(null);
  }, [fetchSensors]);

  // Keep-alive functionality - ping server every 30 seconds to prevent inactivity timeout
  useEffect(() => {
    const keepAlive = async () => {
      try {
        await axios.get('https://aurassure-site.onrender.com');
      } catch (err) {
        // Silently fail - we don't want to disrupt the user experience
        console.debug('Keep-alive ping failed:', err.message);
      }
    };

    // Set up interval to ping every 30 seconds
    const intervalId = setInterval(keepAlive, 30000);

    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  const handleSensorToggle = (sensorId) => {
    setSelectAll(false);
    setSelectedSensors(prev => {
      if (prev.includes(sensorId)) {
        return prev.filter(id => id !== sensorId);
      } else {
        return [...prev, sensorId];
      }
    });
  };

  const handleSelectAll = () => {
    setSelectAll(!selectAll);
    setSelectedSensors([]);
  };

  const handlePreview = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const endpoint = dataSource === 'nebo' 
        ? `${API_BASE_URL}/api/nebo/preview`
        : `${API_BASE_URL}/api/preview`;
      
      const payload = {
        sensors: selectAll ? 'all' : selectedSensors,
        start_time: startTime ? new Date(startTime).toISOString() : null,
        end_time: endTime ? new Date(endTime).toISOString() : null,
        format: format
      };

      const response = await axios.post(endpoint, payload);
      setPreview(response.data);
      setSuccess('Preview loaded successfully!');
    } catch (err) {
      console.error('Error previewing data:', err);
      setError(err.response?.data?.error || 'Failed to preview data');
      setPreview(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const endpoint = dataSource === 'nebo' 
        ? `${API_BASE_URL}/api/nebo/download`
        : `${API_BASE_URL}/api/download`;
      
      const payload = {
        sensors: selectAll ? 'all' : selectedSensors,
        start_time: startTime ? new Date(startTime).toISOString() : null,
        end_time: endTime ? new Date(endTime).toISOString() : null,
        format: format
      };

      const response = await axios.post(endpoint, payload, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const filename = dataSource === 'nebo' 
        ? `nebo_data.${format}`
        : `aurassure_data.${format}`;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Data downloaded successfully!');
    } catch (err) {
      console.error('Error downloading data:', err);
      setError(err.response?.data?.error || 'Failed to download data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>Aurassure Data Download</h1>
          <p className="subtitle">Download environmental sensor data from Aurassure or Nebo</p>
        </header>

        <div className="form-container">
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <div className="form-section">
            <h2>Data Source</h2>
            <div className="format-selection">
              <label className="radio-label">
                <input
                  type="radio"
                  value="aurassure"
                  checked={dataSource === 'aurassure'}
                  onChange={(e) => setDataSource(e.target.value)}
                />
                <span className="radio-button">Aurassure</span>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  value="nebo"
                  checked={dataSource === 'nebo'}
                  onChange={(e) => setDataSource(e.target.value)}
                  disabled={!neboEnabled}
                />
                <span className="radio-button">
                  Nebo {!neboEnabled && '(Not Available)'}
                </span>
              </label>
            </div>
          </div>

          <div className="form-section">
            <h2>Sensor Selection</h2>
            <div className="sensor-selection">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={handleSelectAll}
                />
                <span>Select All Sensors</span>
              </label>
              
              {!selectAll && (
                <div className="sensor-grid">
                  {sensors.map(sensor => (
                    <label key={sensor.id || sensor.slug} className="checkbox-label sensor-item">
                      <input
                        type="checkbox"
                        checked={selectedSensors.includes(sensor.id || sensor.slug)}
                        onChange={() => handleSensorToggle(sensor.id || sensor.slug)}
                      />
                      <span>
                        {sensor.name}
                        {sensor.id && ` (ID: ${sensor.id})`}
                        {sensor.slug && dataSource === 'nebo' && ` (${sensor.slug.substring(0, 8)}...)`}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="form-section">
            <h2>Time Range</h2>
            <div className="time-inputs">
              <div className="input-group">
                <label>Start Time</label>
                <input
                  type="datetime-local"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="datetime-input"
                />
              </div>
              <div className="input-group">
                <label>End Time</label>
                <input
                  type="datetime-local"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="datetime-input"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Download Format</h2>
            <div className="format-selection">
              <label className="radio-label">
                <input
                  type="radio"
                  value="csv"
                  checked={format === 'csv'}
                  onChange={(e) => setFormat(e.target.value)}
                />
                <span className="radio-button">CSV</span>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  value="json"
                  checked={format === 'json'}
                  onChange={(e) => setFormat(e.target.value)}
                />
                <span className="radio-button">JSON</span>
              </label>
            </div>
          </div>

          <div className="button-group">
            <button
              className="btn btn-secondary"
              onClick={handlePreview}
              disabled={loading || (!selectAll && selectedSensors.length === 0)}
            >
              {loading ? 'Loading...' : 'Preview Data'}
            </button>
            <button
              className="btn btn-primary"
              onClick={handleDownload}
              disabled={loading || (!selectAll && selectedSensors.length === 0)}
            >
              {loading ? 'Downloading...' : 'Download Data'}
            </button>
          </div>
        </div>

        {preview && (
          <div className="preview-container">
            <h2>Data Preview</h2>
            <p className="preview-info">
              Showing first 10 rows of {preview.total_rows} total rows
            </p>
            <div className="table-container">
              <table className="preview-table">
                <thead>
                  <tr>
                    {preview.columns.map(col => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.preview.map((row, idx) => (
                    <tr key={idx}>
                      {preview.columns.map(col => (
                        <td key={col}>{String(row[col])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
