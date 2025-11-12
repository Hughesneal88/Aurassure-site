"""
Utility module for fetching secrets from Google Secret Manager.
Falls back to environment variables for local development.
"""
import os
from google.cloud import secretmanager


def get_secret(secret_id, project_id=None):
    """
    Fetch a secret from Google Secret Manager.
    Falls back to environment variable if running locally.
    
    Args:
        secret_id: The ID of the secret to fetch
        project_id: GCP project ID (optional, will auto-detect in GCP)
    
    Returns:
        The secret value as a string
    """
    # Try to get from environment variable first (for local development)
    env_value = os.getenv(secret_id)
    
    # If running on GCP (detected by presence of specific env vars), use Secret Manager
    # Otherwise, use the environment variable (local development)
    if os.getenv('GAE_ENV', '').startswith('standard') or os.getenv('K_SERVICE'):
        # Running on App Engine or Cloud Run - use Secret Manager
        try:
            # Create the Secret Manager client
            client = secretmanager.SecretManagerServiceClient()
            
            # If project_id is not provided, try to get it from environment
            if not project_id:
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT')
            
            if not project_id:
                raise ValueError("Project ID is required when running on GCP")
            
            # Build the resource name of the secret version
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            
            # Access the secret version
            response = client.access_secret_version(request={"name": name})
            
            # Return the decoded payload
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            print(f"Error fetching secret {secret_id} from Secret Manager: {e}")
            # Fall back to environment variable if Secret Manager fails
            if env_value:
                print(f"Falling back to environment variable for {secret_id}")
                return env_value
            raise
    else:
        # Local development - use environment variable
        if env_value:
            return env_value
        else:
            raise ValueError(f"Environment variable {secret_id} not found for local development")
