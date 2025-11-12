# Google Cloud Platform Deployment Guide

This guide explains how to deploy the Aurassure Data Download Site to Google Cloud Platform using different deployment options.

## Prerequisites

1. **Google Cloud Account**: Create an account at [cloud.google.com](https://cloud.google.com)
2. **Google Cloud SDK**: Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. **Project Setup**: Create a new GCP project or use an existing one
4. **Environment Variables**: Your Aurassure API credentials (AccessId and AccessKey)

## Deployment Options

### Option 1: Google App Engine (Recommended for beginners)

App Engine is a fully managed, serverless platform that automatically handles infrastructure.

#### Setup Steps

1. **Initialize gcloud CLI**:
   ```bash
   gcloud init
   gcloud auth login
   ```

2. **Set your project**:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Build the React frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Set environment variables** in Google Cloud Console:
   - Go to [App Engine Settings](https://console.cloud.google.com/appengine/settings)
   - Navigate to "Environment variables"
   - Add:
     - `AccessId`: Your Aurassure Access ID
     - `AccessKey`: Your Aurassure Access Key

5. **Deploy to App Engine**:
   ```bash
   gcloud app deploy
   ```

6. **View your application**:
   ```bash
   gcloud app browse
   ```

#### Updating the Application

To deploy updates, simply run:
```bash
cd frontend && npm run build && cd ..
gcloud app deploy
```

### Option 2: Google Cloud Run (Container-based)

Cloud Run allows you to deploy containerized applications with more control.

#### Setup Steps

1. **Build the Docker image**:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aurassure-app
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy aurassure-app \
     --image gcr.io/YOUR_PROJECT_ID/aurassure-app \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars AccessId=YOUR_ACCESS_ID,AccessKey=YOUR_ACCESS_KEY
   ```

3. **Access your application**:
   - Cloud Run will provide a URL like: `https://aurassure-app-xxxxx.run.app`

#### Updating the Application

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aurassure-app
gcloud run deploy aurassure-app --image gcr.io/YOUR_PROJECT_ID/aurassure-app
```

### Option 3: Automated CI/CD with Cloud Build

For automatic deployments on git push, use Cloud Build.

#### Setup Steps

1. **Connect your GitHub repository**:
   - Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
   - Click "Connect Repository"
   - Follow the prompts to connect your GitHub repository

2. **Create a build trigger**:
   - Click "Create Trigger"
   - Name: `deploy-aurassure-app`
   - Event: Push to branch
   - Branch: `^main$` (or your preferred branch)
   - Configuration: Cloud Build configuration file
   - Location: `/cloudbuild.yaml`

3. **Set environment variables**:
   - In Cloud Build settings, add substitution variables
   - Or use Secret Manager for sensitive data

4. **Push to trigger deployment**:
   ```bash
   git push origin main
   ```

## Environment Variables

### Required Variables
- `AccessId`: Your Aurassure API Access ID
- `AccessKey`: Your Aurassure API Access Key

### Optional Variables
- `PORT`: The port to run the application on (default: 8080 for GCP)
- `DEBUG`: Set to "True" for debug mode (only use in development)

### Setting Environment Variables

**App Engine**:
```yaml
# In app.yaml
env_variables:
  AccessId: "your_access_id"
  AccessKey: "your_access_key"
```

**Cloud Run**:
```bash
gcloud run deploy aurassure-app \
  --set-env-vars AccessId=YOUR_ACCESS_ID,AccessKey=YOUR_ACCESS_KEY
```

**Using Secret Manager** (Recommended for production):
```bash
# Create secrets
echo -n "your_access_id" | gcloud secrets create aurassure-access-id --data-file=-
echo -n "your_access_key" | gcloud secrets create aurassure-access-key --data-file=-

# Deploy Cloud Run with secrets
gcloud run deploy aurassure-app \
  --set-secrets=AccessId=aurassure-access-id:latest,AccessKey=aurassure-access-key:latest
```

## Cost Optimization

### App Engine
- Uses automatic scaling
- Free tier includes 28 instance hours per day
- Configure `min_instances: 0` in app.yaml to scale to zero when not in use

### Cloud Run
- Pay only for actual usage
- Scales to zero automatically
- Free tier includes 2 million requests per month

## Monitoring and Logs

**View logs**:
```bash
# App Engine
gcloud app logs tail

# Cloud Run
gcloud run services logs read aurassure-app
```

**Access Cloud Console**:
- App Engine: https://console.cloud.google.com/appengine
- Cloud Run: https://console.cloud.google.com/run
- Logs: https://console.cloud.google.com/logs

## Troubleshooting

### Build fails
- Ensure frontend builds successfully: `cd frontend && npm run build`
- Check that all dependencies are listed in requirements.txt
- Review build logs in Cloud Console

### Application errors
- Check logs using the commands above
- Verify environment variables are set correctly
- Ensure API credentials are valid

### CORS issues
- The Flask backend is configured with CORS enabled
- If issues persist, check that the backend URL is correct

## Security Best Practices

1. **Never commit credentials**: Use environment variables or Secret Manager
2. **Use HTTPS**: All GCP deployments use HTTPS by default
3. **Restrict API access**: Use IAM roles to control who can deploy
4. **Enable authentication**: Add authentication for sensitive applications
5. **Regular updates**: Keep dependencies updated for security patches

## Additional Resources

- [App Engine Documentation](https://cloud.google.com/appengine/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator)

## Support

For issues specific to this deployment:
1. Check the logs in Cloud Console
2. Review the deployment guide above
3. Contact your system administrator

For Aurassure API issues, refer to the Aurassure documentation.
