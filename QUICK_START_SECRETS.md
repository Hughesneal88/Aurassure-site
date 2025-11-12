# Google Secret Manager Integration - Quick Start

## What Changed?

The Aurassure site now uses **Google Secret Manager** to securely store API credentials instead of environment variables in `app.yaml`. This provides better security and easier credential management.

## For Developers (Local Development)

Nothing changes for local development! You can still use `.env` files:

1. Create a `.env` file in the root directory:
   ```
   AccessId=your_access_id_here
   AccessKey=your_access_key_here
   ```

2. Run the application normally:
   ```bash
   ./start.sh   # Linux/Mac
   ./start.ps1  # Windows
   ```

The application automatically detects it's running locally and uses `.env` files.

## For Deployment to Google Cloud

### First-Time Setup (One-time only)

1. **Create secrets in Google Secret Manager**:
   ```bash
   # Set your project ID
   export PROJECT_ID="your-project-id"
   gcloud config set project $PROJECT_ID
   
   # Create the secrets (replace with your actual credentials)
   echo -n "your_actual_access_id" | gcloud secrets create AccessId --data-file=-
   echo -n "your_actual_access_key" | gcloud secrets create AccessKey --data-file=-
   ```

2. **Grant access to App Engine**:
   ```bash
   # Allow App Engine to read secrets
   gcloud projects add-iam-policy-binding $PROJECT_ID \
       --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"
   ```

3. **For GitHub Actions (if using CI/CD)**:
   ```bash
   # Replace with your GitHub Actions service account email
   SERVICE_ACCOUNT_EMAIL="your-github-sa@your-project.iam.gserviceaccount.com"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
       --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
       --role="roles/secretmanager.secretAccessor"
   ```

### Deploying the Application

After the one-time setup above, deploy normally:

```bash
cd frontend
npm ci
npm run build
cd ..

gcloud app deploy --project=$PROJECT_ID
```

Or use GitHub Actions by pushing to the `main` branch.

## How It Works

- **Local Development**: Uses `.env` files (via `python-dotenv`)
- **Google Cloud**: Automatically uses Secret Manager to fetch credentials
- **Fallback**: If Secret Manager fails, falls back to environment variables

## Detailed Documentation

For complete setup instructions and troubleshooting, see:
- [SECRET_MANAGER_SETUP.md](SECRET_MANAGER_SETUP.md) - Complete Secret Manager setup guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment documentation

## Troubleshooting

**Error: Permission denied when accessing secrets**
- Ensure the service account has `roles/secretmanager.secretAccessor` role
- Verify secrets exist: `gcloud secrets list`

**Error: Secrets not found**
- Secret names must be exactly `AccessId` and `AccessKey` (case-sensitive)
- Verify you're in the correct project: `gcloud config get-value project`

**Local development not working**
- Ensure you have a `.env` file in the root directory
- Check that `AccessId` and `AccessKey` are set in the `.env` file
