# Quick Start Guide for GitHub Pages + Render

This is a condensed guide to get your Aurassure site deployed using GitHub Pages (frontend) and Render (backend) quickly.

## Prerequisites Checklist

- [ ] GitHub account with this repository
- [ ] Render account ([Sign up free](https://render.com))
- [ ] Aurassure API credentials (AccessId and AccessKey)

## 10-Minute Deployment

### Part 1: Deploy Backend to Render (5 minutes)

#### Step 1: Create Render Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select this repository: `Aurassure-site`

#### Step 2: Configure Service

Use these settings:

| Setting | Value |
|---------|-------|
| **Name** | `aurassure-backend` |
| **Region** | (Choose closest to you) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app` |

#### Step 3: Add Environment Variables

In the Environment section, add:

- `AccessId` = Your Aurassure Access ID
- `AccessKey` = Your Aurassure Access Key
- `CORS_ORIGINS` = `*` (or set to your GitHub Pages URL later for better security)

#### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait 3-5 minutes for deployment
3. **Copy your service URL** (e.g., `https://aurassure-backend-xxxx.onrender.com`)

### Part 2: Deploy Frontend to GitHub Pages (5 minutes)

#### Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under "Source", select **"GitHub Actions"**

#### Step 2: Set Backend URL Variable

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"Variables"** tab → **"New repository variable"**
3. Set:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: Your Render URL from Part 1 (e.g., `https://aurassure-backend-xxxx.onrender.com`)
4. Click **"Add variable"**

#### Step 3: Deploy Frontend

**Option A: Automatic (via push to main)**
```bash
git push origin main
```

**Option B: Manual**
1. Go to **Actions** tab
2. Select **"Deploy Frontend to GitHub Pages"**
3. Click **"Run workflow"** → **"Run workflow"**

#### Step 4: Access Your App

After deployment completes (~2 minutes):
- Your app will be at: `https://yourusername.github.io/Aurassure-site/`
- Or your custom domain if configured

Your app is now live! 🎉

## Verification Steps

### 1. Test Backend
```bash
curl https://your-backend-url.onrender.com/api/health
```

Expected response:
```json
{"status":"ok","message":"Aurassure API is running"}
```

### 2. Test Frontend
1. Navigate to your GitHub Pages URL
2. The site should load with the Aurassure interface
3. Try clicking "Preview Data" to test the connection

## Common Issues & Solutions

### Backend Issues

**Problem: Service won't start**
- Check logs in Render dashboard
- Verify environment variables are set correctly
- Ensure Python version is compatible (3.8+)

**Problem: API returns errors**
- Verify Aurassure credentials are correct
- Check API limits on Aurassure platform

**Problem: Slow first response**
- Free tier services sleep after 15 min of inactivity
- First request takes 30-60 seconds to wake up
- Consider upgrading to paid plan ($7/month) for always-on service

### Frontend Issues

**Problem: Build fails in GitHub Actions**
- Check Actions logs for errors
- Verify `REACT_APP_API_URL` variable is set
- Ensure `node_modules` is not committed

**Problem: CORS errors**
- Set `CORS_ORIGINS` in Render to your GitHub Pages URL
- Example: `https://yourusername.github.io`
- Or use `*` for testing (less secure)

**Problem: 404 on page refresh**
- Verify `.nojekyll` file exists in `frontend/public/`
- Should be automatically included in build

### Connection Issues

**Problem: Frontend can't reach backend**
- Verify `REACT_APP_API_URL` is set correctly
- Check browser console for errors
- Ensure backend is running (check Render dashboard)
- Verify CORS is configured correctly

## Update Your Deployment

### Update Backend
1. Push changes to `main` branch
2. Render auto-deploys (watch in dashboard)

### Update Frontend
1. Push changes to `main` branch
2. GitHub Actions auto-deploys (watch in Actions tab)

## Using render.yaml (Alternative)

For infrastructure as code deployment:

1. Ensure `render.yaml` is in your repository root
2. In Render dashboard, select "New" → "Blueprint"
3. Connect your repository
4. Render will read `render.yaml` and create services automatically
5. Add environment variables when prompted

## Cost Overview

### Free Tier Limits

**Render:**
- ✅ 750 hours/month (one service always-on)
- ✅ Services spin down after 15 min idle
- ✅ 512 MB RAM
- ✅ Shared CPU

**GitHub Pages:**
- ✅ 1 GB storage
- ✅ 100 GB bandwidth/month
- ✅ Completely free for public repos

### Upgrade Options

- **Render Starter**: $7/month - Always-on, faster instance
- **GitHub Pro**: $4/month - Private repos only

## Security Best Practices

1. **Never commit secrets**: Use environment variables
2. **Set specific CORS origins**: Replace `*` with your GitHub Pages URL
3. **Update dependencies regularly**: Run `npm audit` and `pip list --outdated`
4. **Monitor logs**: Check Render and GitHub Actions regularly

## Next Steps

- [ ] Set up custom domain (optional)
- [ ] Configure CORS for specific origin
- [ ] Enable monitoring/alerts in Render
- [ ] Set up error tracking (e.g., Sentry)
- [ ] Consider upgrading to paid tier for production

## Support

For detailed documentation:
- GitHub Pages + Render: [DEPLOYMENT_GITHUB_RENDER.md](DEPLOYMENT_GITHUB_RENDER.md)
- Google Cloud: [DEPLOYMENT.md](DEPLOYMENT.md)
- General info: [README.md](README.md)

## Quick Reference Commands

```bash
# Test backend health
curl https://your-backend.onrender.com/api/health

# Trigger frontend deployment
git push origin main

# View GitHub Actions logs
# Go to: repository → Actions tab

# View Render logs
# Go to: dashboard.render.com → your service → Logs
```
