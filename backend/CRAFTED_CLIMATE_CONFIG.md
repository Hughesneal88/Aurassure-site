# Crafted Climate Configuration

This document explains how to configure Crafted Climate sensor AUIDs for the Aurassure application.

## Configuration File

The Crafted Climate sensor AUIDs are stored in a JSON configuration file located at:
```
backend/crafted_climate_auids.json
```

This file is not committed to version control and will be provided during production deployment.

## File Format

The configuration file should follow this JSON structure:

```json
{
  "auids": [
    {
      "id": "AU-001-CC1N-01",
      "name": "Crafted Climate Sensor 1",
      "description": "Optional description of the sensor"
    },
    {
      "id": "AU-001-CC1N-02",
      "name": "Crafted Climate Sensor 2",
      "description": "Optional description of the sensor"
    }
  ]
}
```

### Fields

- **id** (required): The unique AUID identifier for the Crafted Climate sensor
- **name** (required): A human-readable name for the sensor
- **description** (optional): Additional information about the sensor

## Setup Instructions

### For Development

1. Copy the example file:
   ```bash
   cp backend/crafted_climate_auids.json.example backend/crafted_climate_auids.json
   ```

2. Edit `backend/crafted_climate_auids.json` with your test sensor AUIDs

3. Set your API key in the `.env` file:
   ```
   CRAFTED_CLIMATE_API_KEY=your_api_key_here
   ```

### For Production

The production `crafted_climate_auids.json` file will be provided separately and should be placed in the `backend/` directory before deployment.

## Backward Compatibility

For backward compatibility, you can still configure a single sensor using the environment variable:
```
CRAFTED_CLIMATE_AUID=AU-001-CC1N-01
```

If the configuration file exists, it will take precedence over the environment variable.

## Verification

To verify your configuration:

1. Start the backend server
2. Check the startup logs for: `Crafted Climate integration enabled`
3. Access the health endpoint: `GET /api/health`
   - Response should show `"crafted_climate_enabled": true`
4. List sensors: `GET /api/crafted-climate/sensors`
   - Response should show all configured sensors

## Security Notes

- The `crafted_climate_auids.json` file is excluded from version control via `.gitignore`
- Only the API key should be stored in environment variables
- The AUID configuration file can be safely backed up and version controlled separately if needed
