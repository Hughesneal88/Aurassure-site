# Google Secret Manager Setup Guide

This guide explains how to set up Google Secret Manager for storing Aurassure API credentials.

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and configured
- Aurassure API credentials (AccessId and AccessKey)

## Step 1: Create Secrets in Secret Manager

Run the following commands to create secrets in Google Secret Manager:

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Create the AccessId secret
echo -n "your_actual_access_id" | gcloud secrets create AccessId \
    --data-file=- \
    --replication-policy="automatic"

# Create the AccessKey secret
echo -n "your_actual_access_key" | gcloud secrets create AccessKey \
    --data-file=- \
    --replication-policy="automatic"
```

**Important**: Replace `your_actual_access_id` and `your_actual_access_key` with your real Aurassure credentials.

## Step 2: Grant Access to App Engine Service Account

The App Engine default service account needs permission to access these secrets:

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant Secret Manager Secret Accessor role to App Engine service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Step 3: Verify Secrets

List and verify your secrets:

```bash
# List all secrets
gcloud secrets list

# View secret metadata (not the actual value)
gcloud secrets describe AccessId
gcloud secrets describe AccessKey
```

## Step 4: Deploy Your Application

Now you can deploy your application using App Engine:

```bash
# Build frontend
cd frontend
npm ci
npm run build
cd ..

# Deploy to App Engine
gcloud app deploy --project=$PROJECT_ID
```

## Updating Secrets

To update a secret value:

```bash
# Add a new version of the secret
echo -n "new_access_id_value" | gcloud secrets versions add AccessId --data-file=-
```

The application will automatically use the latest version of the secret.

## For GitHub Actions Deployment

Ensure your GitHub Actions service account has the following roles:

1. **App Engine Admin** (`roles/appengine.appAdmin`) - For deploying to App Engine
2. **Secret Manager Secret Accessor** (`roles/secretmanager.secretAccessor`) - For accessing secrets during deployment
3. **Service Account User** (`roles/iam.serviceAccountUser`) - For acting as the App Engine service account

Grant these permissions:

```bash
# Replace SERVICE_ACCOUNT_EMAIL with your GitHub Actions service account email
SERVICE_ACCOUNT_EMAIL="your-github-actions-sa@your-project.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/appengine.appAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/iam.serviceAccountUser"
```

## For Cloud Run Deployment

If deploying to Cloud Run instead of App Engine:

```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/$PROJECT_ID/aurassure-app

# Deploy to Cloud Run with secret references
gcloud run deploy aurassure-app \
    --image gcr.io/$PROJECT_ID/aurassure-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --update-secrets=AccessId=AccessId:latest,AccessKey=AccessKey:latest
```

## Local Development

For local development, the application will fall back to using `.env` files:

1. Create a `.env` file in the root directory:
   ```
   AccessId=your_access_id_here
   AccessKey=your_access_key_here
   ```

2. Run the application normally:
   ```bash
   python backend/app.py
   ```

The code automatically detects whether it's running on GCP and uses Secret Manager only in production.

## Troubleshooting

### Error: Permission Denied

If you get permission errors:
1. Verify the service account has `roles/secretmanager.secretAccessor` role
2. Check that the secrets exist: `gcloud secrets list`
3. Ensure you're using the correct project ID

### Error: Secret Not Found

If secrets are not found:
1. Verify secrets exist: `gcloud secrets list`
2. Check secret names match exactly: `AccessId` and `AccessKey` (case-sensitive)
3. Ensure you're in the correct GCP project: `gcloud config get-value project`

### Application Uses Wrong Credentials

If the application uses environment variables instead of Secret Manager:
1. Verify you're running on GCP (check for `GAE_ENV` or `K_SERVICE` environment variables)
2. Check application logs for any error messages about Secret Manager
3. Ensure the `google-cloud-secret-manager` library is installed

## Security Best Practices

1. **Never commit secrets to version control** - Use Secret Manager for production
2. **Rotate secrets regularly** - Add new versions to Secret Manager periodically
3. **Use least-privilege access** - Only grant Secret Manager access to accounts that need it
4. **Audit access** - Review Cloud Audit Logs for secret access
5. **Use separate secrets for different environments** - Consider using different secrets for staging/production

## Additional Resources

- [Google Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [App Engine Environment Variables](https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables)
- [IAM Roles for Secret Manager](https://cloud.google.com/secret-manager/docs/access-control)
