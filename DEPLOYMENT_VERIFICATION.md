# Deployment Verification Guide

This guide helps verify that the Google Cloud Platform deployment is configured correctly and will work as expected.

## Pre-Deployment Checklist

Before deploying to Google Cloud, verify the following:

### 1. Frontend Build Process

The deployment relies on Cloud Build to compile the React frontend. Verify this works:

```bash
cd frontend
npm ci
npm run build
cd ..
```

Expected output:
- A `frontend/build/` directory should be created
- Should contain `index.html`, `static/` directory, and other assets
- No errors during the build process

### 2. Verify .gcloudignore Configuration

The `.gcloudignore` file must NOT exclude the `frontend/build/` directory. Check:

```bash
# This should show that frontend/build/ is NOT in .gcloudignore
grep -E "^build/|^frontend/build/" .gcloudignore
```

Expected: These patterns should NOT be present. Only specific patterns like `backend/build/` should exist.

### 3. Verify app.yaml Handlers

The `app.yaml` file should have the correct handler configuration:

```yaml
handlers:
  # API routes
  - url: /api/.*
    script: auto
    secure: always

  # Static files (CSS, JS bundles)
  - url: /static/.*
    static_dir: frontend/build/static
    secure: always

  # Other static assets (favicon, manifest, etc.)
  - url: /(.*\.(json|ico|png|jpg|jpeg|gif|svg|webp))$
    static_files: frontend/build/\1
    upload: frontend/build/.*\.(json|ico|png|jpg|jpeg|gif|svg|webp)$
    secure: always

  # SPA routing - serve index.html for all other routes
  - url: /.*
    static_files: frontend/build/index.html
    upload: frontend/build/index.html
    secure: always
```

**Important**: The static file handler must use `/static/.*` (with wildcard) to match all static file paths.

### 4. Verify cloudbuild.yaml

The Cloud Build configuration should build the frontend before deploying:

```yaml
steps:
  - name: 'node:18'
    dir: 'frontend'
    args: ['npm', 'ci']
    
  - name: 'node:18'
    dir: 'frontend'
    args: ['npm', 'run', 'build']
    
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['app', 'deploy', '--quiet']
```

## Deployment Steps

### Option 1: Using Cloud Build (Recommended)

If you have Cloud Build triggers set up:

```bash
git push origin main
```

The Cloud Build trigger will:
1. Install frontend dependencies
2. Build the React app
3. Deploy to App Engine

### Option 2: Manual Deployment

```bash
# 1. Build the frontend
cd frontend
npm ci
npm run build
cd ..

# 2. Deploy to App Engine
gcloud app deploy

# 3. View the deployed app
gcloud app browse
```

## Post-Deployment Verification

After deployment, verify the application is working:

### 1. Check Homepage

Visit your App Engine URL. You should see the Aurassure Data Download Site homepage, not a "Not Found" error.

```bash
gcloud app browse
```

### 2. Check Static Files

Open browser DevTools (F12) and check the Network tab. Verify:
- CSS files load from `/static/css/main.*.css` (Status: 200)
- JS files load from `/static/js/main.*.js` (Status: 200)
- No 404 errors for static assets

### 3. Check API Endpoints

Test the backend API:

```bash
# Get your app URL
APP_URL=$(gcloud app browse --no-launch-browser)

# Test health endpoint
curl $APP_URL/api/health

# Expected response:
# {"status":"ok","message":"Aurassure API is running"}
```

### 4. Check Application Logs

View logs to ensure no errors:

```bash
gcloud app logs tail
```

Look for:
- No "File not found" errors
- No 404 errors for static files
- Successful startup messages

## Troubleshooting

### Issue: "Not Found" Error on Homepage

**Cause**: Frontend build files were not uploaded or are in the wrong location.

**Solution**:
1. Verify `.gcloudignore` does NOT exclude `frontend/build/`
2. Verify `cloudbuild.yaml` includes frontend build steps
3. Check that `app.yaml` handlers point to `frontend/build/` directory

### Issue: Static Files Return 404

**Cause**: Static file handler URL pattern is incorrect.

**Solution**:
1. Verify the static handler uses `/static/.*` (with wildcard)
2. Check that files exist in `frontend/build/static/` directory
3. Review handler order in `app.yaml` (API routes should come first)

### Issue: API Routes Return 404

**Cause**: API handler might be shadowed by static file handlers.

**Solution**:
1. Ensure `/api/.*` handler is listed FIRST in the handlers section
2. Verify Flask app is running with the correct entrypoint

### Issue: Build Fails in Cloud Build

**Cause**: Frontend dependencies or build script issues.

**Solution**:
1. Test the build locally: `cd frontend && npm ci && npm run build`
2. Check Cloud Build logs for specific error messages
3. Verify Node.js version matches (uses node:18 in cloudbuild.yaml)

## Key Files to Check

When debugging deployment issues, check these files:

1. **`.gcloudignore`** - Must NOT exclude `frontend/build/`
2. **`app.yaml`** - Handler configuration for serving files
3. **`cloudbuild.yaml`** - Build process configuration
4. **`frontend/package.json`** - Build script definition
5. **`requirements.txt`** - Must include `gunicorn`

## Environment Variables

Don't forget to set these in Google Cloud Console:

```bash
# App Engine > Settings > Environment Variables
AccessId=your_aurassure_access_id
AccessKey=your_aurassure_access_key
```

Or use Secret Manager for better security.

## Summary of the Fix

The original issue was caused by:
1. `.gcloudignore` had a `build/` pattern that excluded the `frontend/build/` directory
2. Without the frontend build files, App Engine couldn't serve the React application
3. All requests returned "Not Found" errors

The fix:
1. Changed `.gcloudignore` to only exclude Python build artifacts (`backend/build/`)
2. Ensured `frontend/build/` directory is uploaded during deployment
3. Fixed `app.yaml` static handler to use `/static/.*` pattern
4. Cloud Build now successfully builds frontend and deploys all necessary files

## Support

For additional help:
- Review [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions
- Check Google Cloud logs: https://console.cloud.google.com/logs
- Review App Engine documentation: https://cloud.google.com/appengine/docs
