#!/bin/bash
# Local development script
# Requires GCP credentials and environment setup

set -e

# TODO: Replace with your project ID
export GCP_PROJECT_ID="YOUR_PROJECT_ID"

echo "🔧 Starting LexGuard RiskScope Backend (Local Development)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check GCP authentication
echo "🔐 Checking GCP authentication..."
if ! gcloud auth application-default print-access-token &> /dev/null; then
    echo "⚠️  No GCP credentials found. Running authentication..."
    gcloud auth application-default login
fi

# Start the server
echo ""
echo "🚀 Starting server on http://localhost:8080"
echo "📖 API docs available at http://localhost:8080/docs"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8080
