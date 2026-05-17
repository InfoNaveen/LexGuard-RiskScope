#!/bin/bash
# Setup script for LexGuard RiskScope Backend
# TODO: Replace YOUR_PROJECT_ID with actual GCP project ID
# TODO: Replace YOUR_REGION with target region (e.g., us-central1)
# TODO: Replace YOUR_GEMINI_API_KEY with actual Gemini API key

set -e

PROJECT_ID="YOUR_PROJECT_ID"
REGION="YOUR_REGION"
SERVICE_ACCOUNT="svc-lexguard-backend"

echo "🚀 Setting up LexGuard RiskScope Backend..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Set project
echo "📋 Setting GCP project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create service account
echo "👤 Creating service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT \
    --display-name="LexGuard Backend Service Account" \
    --project=$PROJECT_ID || echo "Service account already exists"

# Grant IAM roles
echo "🔐 Granting IAM roles..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# Initialize Firestore
echo "🔥 Initializing Firestore..."
gcloud firestore databases create --location=$REGION --project=$PROJECT_ID || echo "Firestore already initialized"

# Create secret for Gemini API key
echo "🔑 Creating secret for Gemini API key..."
echo "Please enter your Gemini API key:"
read -s GEMINI_API_KEY

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Gemini API key cannot be empty"
    exit 1
fi

echo -n "$GEMINI_API_KEY" | gcloud secrets create lexguard-gemini-api-key \
    --data-file=- \
    --project=$PROJECT_ID || echo "Secret already exists"

# Grant service account access to secret
echo "🔓 Granting service account access to secret..."
gcloud secrets add-iam-policy-binding lexguard-gemini-api-key \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update config.py with PROJECT_ID: $PROJECT_ID"
echo "2. Update cloudbuild.yaml with PROJECT_ID and REGION"
echo "3. Deploy with: gcloud builds submit --config=cloudbuild.yaml"
echo ""
