#!/bin/bash
# Deployment script for LexGuard RiskScope Backend
# TODO: Replace YOUR_PROJECT_ID with actual GCP project ID
# TODO: Replace YOUR_REGION with target region (e.g., us-central1)

set -e

PROJECT_ID="YOUR_PROJECT_ID"
REGION="YOUR_REGION"

echo "🚀 Deploying LexGuard RiskScope Backend..."

# Validate configuration
if [ "$PROJECT_ID" = "YOUR_PROJECT_ID" ]; then
    echo "❌ Please update PROJECT_ID in deploy.sh"
    exit 1
fi

if [ "$REGION" = "YOUR_REGION" ]; then
    echo "❌ Please update REGION in deploy.sh"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Submit build
echo "🔨 Building and deploying..."
gcloud builds submit --config=cloudbuild.yaml --project=$PROJECT_ID

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Service URL:"
gcloud run services describe lexguard-backend \
    --platform=managed \
    --region=$REGION \
    --format='value(status.url)'
echo ""
