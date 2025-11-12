# Google Secret Manager Integration - Implementation Summary

## Overview

This implementation adds Google Secret Manager integration to the Aurassure Data Download Site, replacing the previous approach of storing API credentials in environment variables or `app.yaml`.

## What Was Changed

### 1. Dependencies Added
- **File**: `requirements.txt`, `backend/requirements.txt`
- **Change**: Added `google-cloud-secret-manager==2.20.0`

### 2. New Secrets Utility Module
- **File**: `backend/secrets_util.py` (new)
- **Purpose**: Handles fetching secrets from Google Secret Manager
- **Features**:
  - Automatically detects if running on GCP (App Engine or Cloud Run)
  - Uses Secret Manager when running on GCP
  - Falls back to environment variables for local development
  - Secure error handling without logging sensitive data

### 3. Updated Credential Loading
- **File**: `backend/aurasure.py`
- **Change**: Now uses `secrets_util.get_secret()` instead of directly calling `os.getenv()`
- **Behavior**:
  - Production (GCP): Fetches from Secret Manager
  - Local development: Uses `.env` files
  - Automatic fallback mechanism

### 4. App Engine Configuration
- **File**: `app.yaml`
- **Change**: Removed hardcoded environment variables
- **Added**: `GOOGLE_CLOUD_PROJECT` environment variable for Secret Manager

### 5. GitHub Actions Workflow
- **File**: `.github/workflows/deploy-gcp.yml`
- **Change**: Added comments documenting required IAM roles
- **Required Roles**:
  - `roles/appengine.appAdmin`
  - `roles/secretmanager.secretAccessor`
  - `roles/iam.serviceAccountUser`

### 6. Documentation
- **New Files**:
  - `SECRET_MANAGER_SETUP.md` - Comprehensive setup guide
  - `QUICK_START_SECRETS.md` - Quick reference for setup
- **Updated Files**:
  - `DEPLOYMENT.md` - Added Secret Manager instructions
  - `README.md` - Added Secret Manager information and prerequisites

## Security Improvements

1. **No credentials in code or configuration files**
   - Secrets are stored in Google Secret Manager
   - No hardcoded credentials in `app.yaml` or code

2. **IAM-based access control**
   - Access to secrets is controlled via IAM policies
   - Service accounts need explicit permission to access secrets

3. **Secure logging**
   - No sensitive data logged to stdout/stderr
   - Error messages don't expose secret values

4. **CodeQL verified**
   - All security vulnerabilities resolved
   - No clear-text logging of sensitive data

## How It Works

### Production (Google Cloud Platform)

1. Application starts on App Engine or Cloud Run
2. `secrets_util.get_secret()` detects GCP environment (via `GAE_ENV` or `K_SERVICE` env vars)
3. Connects to Secret Manager using Application Default Credentials
4. Fetches `AccessId` and `AccessKey` from Secret Manager
5. If Secret Manager fails, falls back to environment variables (for resilience)

### Local Development

1. Application starts locally
2. `secrets_util.get_secret()` detects local environment (no GCP env vars)
3. Returns value from environment variables (loaded from `.env` file)
4. No Secret Manager calls are made

## Setup Requirements

### One-Time Setup (Before First Deployment)

1. **Create secrets in Secret Manager**:
   ```bash
   echo -n "actual_access_id" | gcloud secrets create AccessId --data-file=-
   echo -n "actual_access_key" | gcloud secrets create AccessKey --data-file=-
   ```

2. **Grant access to App Engine service account**:
   ```bash
   PROJECT_ID=$(gcloud config get-value project)
   gcloud projects add-iam-policy-binding $PROJECT_ID \
       --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"
   ```

3. **Grant access to GitHub Actions service account** (if using CI/CD):
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
       --member="serviceAccount:YOUR_GITHUB_SA@your-project.iam.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"
   ```

### Deployment

After one-time setup, deploy normally:
```bash
cd frontend && npm run build && cd ..
gcloud app deploy
```

## Testing

All tests passed:
- ✅ Python syntax validation
- ✅ Import tests (local and GCP modes)
- ✅ Flask app initialization
- ✅ Frontend build
- ✅ Security scan (CodeQL) - 0 vulnerabilities
- ✅ Fallback mechanism verification

## Migration Notes

### For Existing Deployments

If you have an existing deployment with credentials in `app.yaml`:

1. Create secrets in Secret Manager (see Setup Requirements above)
2. Deploy the updated code
3. Verify the application works correctly
4. Remove old environment variables from `app.yaml` (already done in this PR)

### For Local Developers

**No changes required!** Local development continues to use `.env` files as before.

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure service account has `roles/secretmanager.secretAccessor` role
   - Verify with: `gcloud projects get-iam-policy YOUR_PROJECT_ID`

2. **Secret Not Found**
   - Verify secrets exist: `gcloud secrets list`
   - Check secret names are exactly `AccessId` and `AccessKey` (case-sensitive)

3. **Local Development Issues**
   - Ensure `.env` file exists in root directory
   - Verify `AccessId` and `AccessKey` are set in `.env`

## Cost Considerations

- **Secret Manager**: Free for first 6 secret versions
- **Secret Access**: $0.03 per 10,000 access operations
- **Typical Cost**: <$1/month for this application (secrets accessed only on app startup)

## References

- [Google Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [SECRET_MANAGER_SETUP.md](SECRET_MANAGER_SETUP.md) - Detailed setup guide
- [QUICK_START_SECRETS.md](QUICK_START_SECRETS.md) - Quick setup reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment documentation
