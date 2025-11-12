# GitHub Pages + Render Deployment Guide

This guide explains how to deploy the Aurassure Data Download Site with:
- **Frontend**: GitHub Pages (free static site hosting)
- **Backend**: Render (free tier available for web services)

## Overview

- Frontend is hosted as a static site on GitHub Pages
- Backend API runs on Render's web service platform
- Both services offer free tiers suitable for this application

## Prerequisites

1. **GitHub Account**: For hosting the frontend
2. **Render Account**: Create a free account at [render.com](https://render.com)
3. **Environment Variables**: Your Aurassure API credentials (AccessId and AccessKey)

## Part 1: Deploy Backend to Render

### Step 1: Create a Render Web Service

1. **Sign up/Login to Render**: Go to [render.com](https://render.com) and log in
2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `Aurassure-site` repository

### Step 2: Configure the Web Service

Use these settings:

- **Name**: `aurassure-backend` (or any name you prefer)
- **Region**: Choose the closest to your users
- **Branch**: `main`
- **Root Directory**: `backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app`

### Step 3: Add Environment Variables

In the Render dashboard, add these environment variables:

- `AccessId`: Your Aurassure API Access ID
- `AccessKey`: Your Aurassure API Access Key
- `PORT`: `10000` (Render's default, automatically set)
- `CORS_ORIGINS`: Your GitHub Pages URL (e.g., `https://yourusername.github.io`)
  - Optional: Set to `*` to allow all origins (less secure)

### Step 4: Deploy

1. Click "Create Web Service"
2. Render will automatically build and deploy your backend
3. Once deployed, note your service URL (e.g., `https://aurassure-backend-xxxx.onrender.com`)

**Important Notes:**
- Free tier services spin down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds
- Consider upgrading to a paid plan for production use

## Part 2: Deploy Frontend to GitHub Pages

### Step 1: Configure Repository Settings

1. **Enable GitHub Pages**:
   - Go to your repository on GitHub
   - Navigate to Settings → Pages
   - Source: Select "GitHub Actions"

2. **Set Repository Variable**:
   - Go to Settings → Secrets and variables → Actions → Variables
   - Click "New repository variable"
   - Name: `REACT_APP_API_URL`
   - Value: Your Render backend URL (e.g., `https://aurassure-backend-xxxx.onrender.com`)
   - Click "Add variable"

### Step 2: Deploy

The deployment happens automatically via GitHub Actions:

1. **Automatic Deployment**:
   - Push to the `main` branch
   - GitHub Actions will automatically build and deploy the frontend
   - Monitor progress in the "Actions" tab

2. **Manual Deployment** (if needed):
   - Go to Actions tab
   - Select "Deploy Frontend to GitHub Pages" workflow
   - Click "Run workflow" → "Run workflow"

### Step 3: Access Your Application

Once deployed, your application will be available at:
- `https://yourusername.github.io/Aurassure-site/`

Or if you have a custom domain configured:
- `https://yourdomain.com`

## Environment Variables Summary

### Backend (Render)

| Variable | Description | Example |
|----------|-------------|---------|
| `AccessId` | Aurassure API Access ID | `your_access_id` |
| `AccessKey` | Aurassure API Access Key | `your_access_key` |
| `CORS_ORIGINS` | Allowed origins for CORS | `https://yourusername.github.io` |

### Frontend (GitHub Actions)

| Variable | Description | Example |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `https://aurassure-backend-xxxx.onrender.com` |

## Testing Your Deployment

1. **Test Backend**:
   ```bash
   curl https://your-backend-url.onrender.com/api/health
   ```
   Should return: `{"status":"ok","message":"Aurassure API is running"}`

2. **Test Frontend**:
   - Navigate to your GitHub Pages URL
   - The site should load and display the Aurassure Data Download interface
   - Try fetching sensors and previewing data

## Updating Your Application

### Update Backend

1. Push changes to the `main` branch
2. Render automatically detects changes and redeploys
3. Monitor deployment in Render dashboard

### Update Frontend

1. Push changes to the `main` branch
2. GitHub Actions automatically builds and deploys
3. Monitor deployment in GitHub Actions tab

## Troubleshooting

### Backend Issues

**Service not responding:**
- Check if the service is active in Render dashboard
- Free tier services may be spinning up (wait 30-60 seconds)
- Check logs in Render dashboard

**CORS errors:**
- Verify `CORS_ORIGINS` environment variable is set correctly
- Include your GitHub Pages URL without trailing slash

**API errors:**
- Check environment variables are set correctly
- Review logs in Render dashboard
- Verify Aurassure credentials are valid

### Frontend Issues

**Build failures:**
- Check GitHub Actions logs
- Verify `REACT_APP_API_URL` is set in repository variables
- Ensure all dependencies are listed in package.json

**404 errors on refresh:**
- GitHub Pages serves the app correctly
- The `.nojekyll` file should be present in the build

**API connection errors:**
- Verify backend URL in repository variables
- Check browser console for CORS errors
- Ensure backend is running on Render

## Cost Considerations

### Free Tier Limits

**Render Free Tier:**
- 750 hours per month (enough for one always-on service)
- Services spin down after 15 minutes of inactivity
- 512 MB RAM
- Shared CPU

**GitHub Pages:**
- 1 GB storage
- 100 GB bandwidth per month
- Completely free for public repositories

### Upgrading

For production use, consider:
- **Render Starter Plan** ($7/month): Always-on service, more resources
- **GitHub Pro** (if using private repositories): $4/month

## Security Best Practices

1. **Never commit credentials**: Use environment variables
2. **CORS Configuration**: Set specific origins instead of `*`
3. **HTTPS**: Both Render and GitHub Pages use HTTPS by default
4. **API Rate Limiting**: Consider implementing rate limiting on backend
5. **Keep Dependencies Updated**: Regularly update npm and pip packages

## Monitoring

### Render Dashboard
- View logs: Real-time and historical
- Monitor resource usage
- Set up alerts for service issues

### GitHub Actions
- View deployment history
- Monitor build times
- Debug failed deployments

## Custom Domain (Optional)

### For Frontend (GitHub Pages)
1. Add custom domain in repository Settings → Pages
2. Configure DNS with your domain provider
3. Update `CORS_ORIGINS` on Render to include custom domain

### For Backend (Render)
1. Add custom domain in Render service settings
2. Configure DNS with your domain provider
3. Update `REACT_APP_API_URL` in GitHub repository variables

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [GitHub Pages Documentation](https://docs.github.com/pages)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Flask Deployment Best Practices](https://flask.palletsprojects.com/en/latest/deploying/)

## Support

For deployment issues:
1. Check the troubleshooting section above
2. Review logs in Render and GitHub Actions
3. Verify all environment variables are set correctly

For Aurassure API issues, refer to the Aurassure documentation.
