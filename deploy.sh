#!/bin/bash
# deploy.sh - Helper script for deploying to Google Cloud

set -e

echo "Aurassure Site - Google Cloud Deployment Helper"
echo "================================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Error: Not authenticated with gcloud."
    echo "Please run: gcloud auth login"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "Error: No project set."
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "Current project: $PROJECT_ID"
echo ""

# Menu for deployment options
echo "Select deployment option:"
echo "1) App Engine (Managed, serverless)"
echo "2) Cloud Run (Container-based)"
echo "3) Build frontend only"
echo "4) Exit"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Deploying to App Engine..."
        echo "Building frontend..."
        cd frontend
        npm install
        npm run build
        cd ..
        echo "Deploying to App Engine..."
        gcloud app deploy --quiet
        echo ""
        echo "Deployment complete! Opening application..."
        gcloud app browse
        ;;
    2)
        echo ""
        echo "Deploying to Cloud Run..."
        IMAGE_NAME="gcr.io/$PROJECT_ID/aurassure-app"
        echo "Building Docker image: $IMAGE_NAME"
        gcloud builds submit --tag $IMAGE_NAME
        echo ""
        read -p "Enter region (default: us-central1): " REGION
        REGION=${REGION:-us-central1}
        echo "Deploying to Cloud Run in region: $REGION"
        gcloud run deploy aurassure-app \
            --image $IMAGE_NAME \
            --platform managed \
            --region $REGION \
            --allow-unauthenticated
        echo ""
        echo "Deployment complete!"
        echo "Remember to set environment variables (AccessId, AccessKey) in Cloud Console"
        ;;
    3)
        echo ""
        echo "Building frontend only..."
        cd frontend
        npm install
        npm run build
        cd ..
        echo "Frontend build complete! Output in frontend/build/"
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
