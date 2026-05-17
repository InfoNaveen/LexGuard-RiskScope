# Deployment Guide for LexGuard RiskScope Backend

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Gemini API Key** from Google AI Studio
4. **Project ID** chosen and available

## Step-by-Step Deployment

### 1. Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd lexguard-backend

# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"  # or your preferred region

# Update configuration files
sed -i "s/YOUR_PROJECT_ID/$PROJECT_ID/g" config.py
sed -i "s/YOUR_PROJECT_ID/$PROJECT_ID/g" cloudbuild.yaml
sed -i "s/YOUR_REGION/$REGION/g" cloudbuild.yaml
```

### 2. Run Setup Script

```bash
# Make scripts executable
chmod +x setup.sh deploy.sh local_dev.sh

# Run setup (will prompt for Gemini API key)
./setup.sh
```

The setup script will:
- Enable required GCP APIs
- Create service account with minimal permissions
- Initialize Firestore
- Store Gemini API key in Secret Manager
- Configure IAM bindings

### 3. Deploy to Cloud Run

```bash
# Update deploy.sh with your project ID and region
nano deploy.sh

# Deploy
./deploy.sh
```

This will:
- Build Docker container
- Run vulnerability scan
- Deploy to Cloud Run with security settings
- Output the service URL

### 4. Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe lexguard-backend \
    --platform=managed \
    --region=$REGION \
    --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Test health endpoint (will fail if --no-allow-unauthenticated is set)
# You need to authenticate first
gcloud auth print-identity-token | \
    curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
    $SERVICE_URL/health
```

## Authentication Setup

Since the service is deployed with `--no-allow-unauthenticated`, you need to set up authentication:

### Option 1: Cloud Load Balancer with IAP

```bash
# Create backend service
gcloud compute backend-services create lexguard-backend-service \
    --global \
    --load-balancing-scheme=EXTERNAL_MANAGED

# Add Cloud Run NEG
gcloud compute network-endpoint-groups create lexguard-neg \
    --region=$REGION \
    --network-endpoint-type=serverless \
    --cloud-run-service=lexguard-backend

# Add NEG to backend service
gcloud compute backend-services add-backend lexguard-backend-service \
    --global \
    --network-endpoint-group=lexguard-neg \
    --network-endpoint-group-region=$REGION

# Create URL map
gcloud compute url-maps create lexguard-lb \
    --default-service=lexguard-backend-service

# Create SSL certificate (requires domain)
gcloud compute ssl-certificates create lexguard-cert \
    --domains=api.lexguard.example.com

# Create HTTPS proxy
gcloud compute target-https-proxies create lexguard-proxy \
    --url-map=lexguard-lb \
    --ssl-certificates=lexguard-cert

# Create forwarding rule
gcloud compute forwarding-rules create lexguard-forwarding-rule \
    --global \
    --target-https-proxy=lexguard-proxy \
    --ports=443

# Enable IAP
gcloud iap web enable --resource-type=backend-services \
    --service=lexguard-backend-service
```

### Option 2: Service-to-Service Authentication

For backend services calling this API:

```bash
# Grant service account permission to invoke
gcloud run services add-iam-policy-binding lexguard-backend \
    --region=$REGION \
    --member="serviceAccount:caller-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

In calling service:
```python
import google.auth.transport.requests
import google.oauth2.id_token

def make_authenticated_request(url):
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, url)
    
    headers = {"Authorization": f"Bearer {id_token}"}
    response = requests.get(url, headers=headers)
    return response
```

## Environment Variables

Set these in Cloud Run:

```bash
gcloud run services update lexguard-backend \
    --region=$REGION \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID"
```

## Monitoring Setup

### Enable Cloud Monitoring

```bash
# Create notification channel (email)
gcloud alpha monitoring channels create \
    --display-name="LexGuard Alerts" \
    --type=email \
    --channel-labels=email_address=alerts@lexguard.example.com

# Create alert policy for errors
gcloud alpha monitoring policies create \
    --notification-channels=<channel-id> \
    --display-name="LexGuard Error Rate" \
    --condition-display-name="High Error Rate" \
    --condition-threshold-value=10 \
    --condition-threshold-duration=60s
```

### View Logs

```bash
# Stream logs
gcloud run services logs tail lexguard-backend --region=$REGION

# View logs in console
echo "https://console.cloud.google.com/run/detail/$REGION/lexguard-backend/logs?project=$PROJECT_ID"
```

## Scaling Configuration

```bash
# Update scaling settings
gcloud run services update lexguard-backend \
    --region=$REGION \
    --min-instances=1 \
    --max-instances=100 \
    --concurrency=80 \
    --cpu=2 \
    --memory=2Gi \
    --timeout=300
```

## Cost Optimization

### Development Environment
```bash
# Minimal resources for dev
gcloud run services update lexguard-backend \
    --region=$REGION \
    --min-instances=0 \
    --max-instances=5 \
    --concurrency=10 \
    --cpu=1 \
    --memory=1Gi
```

### Production Environment
```bash
# Production settings
gcloud run services update lexguard-backend \
    --region=$REGION \
    --min-instances=2 \
    --max-instances=100 \
    --concurrency=80 \
    --cpu=2 \
    --memory=2Gi
```

## Rollback

```bash
# List revisions
gcloud run revisions list --service=lexguard-backend --region=$REGION

# Rollback to previous revision
gcloud run services update-traffic lexguard-backend \
    --region=$REGION \
    --to-revisions=<previous-revision>=100
```

## Troubleshooting

### Service won't start
```bash
# Check logs
gcloud run services logs read lexguard-backend --region=$REGION --limit=50

# Common issues:
# - Secret not accessible: Check IAM permissions
# - Firestore not initialized: Run setup.sh
# - Wrong project ID: Update config.py
```

### Authentication errors
```bash
# Verify service account
gcloud run services describe lexguard-backend \
    --region=$REGION \
    --format='value(spec.template.spec.serviceAccountName)'

# Check IAM bindings
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:svc-lexguard-backend@$PROJECT_ID.iam.gserviceaccount.com"
```

### Gemini API errors
```bash
# Verify secret exists
gcloud secrets describe lexguard-gemini-api-key --project=$PROJECT_ID

# Check secret access
gcloud secrets versions access latest \
    --secret=lexguard-gemini-api-key \
    --project=$PROJECT_ID
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Deploy
        run: |
          gcloud builds submit --config=cloudbuild.yaml
```

## Maintenance

### Update Dependencies
```bash
# Update requirements.txt
pip list --outdated
pip install --upgrade <package>
pip freeze > requirements.txt

# Redeploy
./deploy.sh
```

### Rotate Secrets
```bash
# Create new secret version
echo -n "NEW_API_KEY" | gcloud secrets versions add lexguard-gemini-api-key \
    --data-file=- \
    --project=$PROJECT_ID

# Cloud Run will automatically use latest version on next deployment
./deploy.sh
```

## Production Checklist

- [ ] Custom domain configured
- [ ] SSL certificate installed
- [ ] Cloud Armor enabled
- [ ] Monitoring alerts configured
- [ ] Log retention policy set
- [ ] Backup strategy for Firestore
- [ ] Disaster recovery plan documented
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Documentation updated
