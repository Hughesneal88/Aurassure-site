# Quick Start Guide for Google Cloud Deployment

This is a condensed guide to get your Aurassure site deployed to Google Cloud quickly.

## Prerequisites Checklist

- [ ] Google Cloud account created
- [ ] gcloud CLI installed ([Download here](https://cloud.google.com/sdk/docs/install))
- [ ] Aurassure API credentials (AccessId and AccessKey)

## 5-Minute Deployment (App Engine)

### Step 1: Setup Google Cloud
```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create aurassure-site --name="Aurassure Site"

# Set the project
gcloud config set project aurassure-site
```

### Step 2: Enable Required APIs
```bash
# Enable App Engine and Cloud Build APIs
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 3: Initialize App Engine
```bash
# Initialize App Engine in your preferred region
gcloud app create --region=us-central
```

### Step 4: Build Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 5: Set Environment Variables
**Option A: Using app.yaml (not recommended for security)**
Edit `app.yaml` and add your credentials:
```yaml
env_variables:
  AccessId: "your_access_id_here"
  AccessKey: "your_access_key_here"
```

**Option B: Using Secret Manager (recommended)**
```bash
# Create secrets
echo -n "your_access_id" | gcloud secrets create aurassure-access-id --data-file=-
echo -n "your_access_key" | gcloud secrets create aurassure-access-key --data-file=-

# Grant App Engine access to secrets
PROJECT_ID=$(gcloud config get-value project)
gcloud secrets add-iam-policy-binding aurassure-access-id \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
  
gcloud secrets add-iam-policy-binding aurassure-access-key \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Then update `main.py` to load from Secret Manager.

### Step 6: Deploy
```bash
gcloud app deploy --quiet
```

### Step 7: Open Your App
```bash
gcloud app browse
```

Your app is now live! 🎉

## Alternative: Cloud Run (Container-based)

If you prefer containers:

```bash
# Build the container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aurassure-app

# Deploy to Cloud Run
gcloud run deploy aurassure-app \
  --image gcr.io/YOUR_PROJECT_ID/aurassure-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AccessId=YOUR_ACCESS_ID,AccessKey=YOUR_ACCESS_KEY
```

## Using the Helper Script

For an interactive deployment experience:

```bash
./deploy.sh
```

Select your preferred deployment method and follow the prompts.

## Troubleshooting

### Error: "gcloud: command not found"
Install the gcloud CLI: https://cloud.google.com/sdk/docs/install

### Error: "API not enabled"
Enable required APIs:
```bash
gcloud services enable appengine.googleapis.com cloudbuild.googleapis.com
```

### Error: Frontend build fails
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
cd ..
```

### Application doesn't load
1. Check logs: `gcloud app logs tail -s default`
2. Verify environment variables are set
3. Ensure frontend was built before deployment

## Next Steps

- Set up custom domain: https://cloud.google.com/appengine/docs/standard/mapping-custom-domains
- Enable Cloud CDN for better performance
- Set up monitoring and alerts
- Configure automatic scaling parameters

## Cost Estimation

**App Engine Free Tier:**
- 28 instance hours per day
- 1 GB outbound data per day
- Shared memcache

**Beyond free tier:** ~$0.05/hour for F2 instance class

Use the [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator) for detailed estimates.

## Support

For detailed documentation, see [DEPLOYMENT.md](DEPLOYMENT.md)
