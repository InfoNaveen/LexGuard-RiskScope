# ✅ Pre-Deployment Checklist

## 🔧 Configuration Updates Required

### 1. Update config.py
```bash
# Line 8: Replace YOUR_PROJECT_ID
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "YOUR_PROJECT_ID")

# Action: Replace with your actual GCP project ID
# Example: GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "lexguard-prod-2024")
```

### 2. Update cloudbuild.yaml
```yaml
# Lines with YOUR_PROJECT_ID (multiple locations):
- 'gcr.io/YOUR_PROJECT_ID/lexguard-backend:$COMMIT_SHA'

# Lines with YOUR_REGION:
- '--region=YOUR_REGION'

# Lines with service account:
- '--service-account=svc-lexguard-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com'

# Action: Replace all instances with actual values
# Example PROJECT_ID: lexguard-prod-2024
# Example REGION: us-central1
```

### 3. Update setup.sh
```bash
# Line 7: Replace YOUR_PROJECT_ID
PROJECT_ID="YOUR_PROJECT_ID"

# Line 8: Replace YOUR_REGION
REGION="YOUR_REGION"

# Action: Replace with your actual values
```

### 4. Update deploy.sh
```bash
# Line 6: Replace YOUR_PROJECT_ID
PROJECT_ID="YOUR_PROJECT_ID"

# Line 7: Replace YOUR_REGION
REGION="YOUR_REGION"

# Action: Replace with your actual values
```

## 🔑 Secrets Required

### 1. Gemini API Key
- [ ] Obtain Gemini API key from: https://makersuite.google.com/app/apikey
- [ ] Keep it secure (will be entered during setup.sh)
- [ ] Never commit to git

### 2. Secret Manager Secret Name
The setup.sh script will create a secret named: `lexguard-gemini-api-key`

If you want a different name:
- [ ] Update config.py line 9: `GEMINI_API_KEY_SECRET = "your-secret-name"`
- [ ] Update setup.sh to use the same name

## 🏗️ GCP Prerequisites

### 1. GCP Project
- [ ] Create GCP project or use existing
- [ ] Enable billing on the project
- [ ] Note the project ID

### 2. gcloud CLI
- [ ] Install gcloud CLI: https://cloud.google.com/sdk/docs/install
- [ ] Authenticate: `gcloud auth login`
- [ ] Set project: `gcloud config set project YOUR_PROJECT_ID`

### 3. Required APIs (setup.sh will enable these)
- [ ] Cloud Run API
- [ ] Firestore API
- [ ] Secret Manager API
- [ ] Container Registry API
- [ ] Cloud Build API

## 📝 Quick Update Script

Run this to update all files at once:

```bash
# Set your values
export PROJECT_ID="your-actual-project-id"
export REGION="us-central1"  # or your preferred region

# Update all files (macOS/Linux)
sed -i '' "s/YOUR_PROJECT_ID/$PROJECT_ID/g" config.py cloudbuild.yaml setup.sh deploy.sh
sed -i '' "s/YOUR_REGION/$REGION/g" cloudbuild.yaml deploy.sh

# For Linux (without the '')
sed -i "s/YOUR_PROJECT_ID/$PROJECT_ID/g" config.py cloudbuild.yaml setup.sh deploy.sh
sed -i "s/YOUR_REGION/$REGION/g" cloudbuild.yaml deploy.sh

# For Windows PowerShell
(Get-Content config.py) -replace 'YOUR_PROJECT_ID', $env:PROJECT_ID | Set-Content config.py
(Get-Content cloudbuild.yaml) -replace 'YOUR_PROJECT_ID', $env:PROJECT_ID | Set-Content cloudbuild.yaml
(Get-Content cloudbuild.yaml) -replace 'YOUR_REGION', $env:REGION | Set-Content cloudbuild.yaml
(Get-Content setup.sh) -replace 'YOUR_PROJECT_ID', $env:PROJECT_ID | Set-Content setup.sh
(Get-Content setup.sh) -replace 'YOUR_REGION', $env:REGION | Set-Content setup.sh
(Get-Content deploy.sh) -replace 'YOUR_PROJECT_ID', $env:PROJECT_ID | Set-Content deploy.sh
(Get-Content deploy.sh) -replace 'YOUR_REGION', $env:REGION | Set-Content deploy.sh
```

## 🚀 Deployment Steps

### Step 1: Verify Updates
```bash
# Check that YOUR_PROJECT_ID is replaced
grep -r "YOUR_PROJECT_ID" config.py cloudbuild.yaml setup.sh deploy.sh

# Should return no results if all updated correctly
```

### Step 2: Make Scripts Executable
```bash
chmod +x setup.sh deploy.sh local_dev.sh
```

### Step 3: Run Setup
```bash
./setup.sh
# When prompted, paste your Gemini API key
```

### Step 4: Deploy
```bash
./deploy.sh
```

### Step 5: Test
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe lexguard-backend \
    --region=$REGION \
    --format='value(status.url)')

# Test health endpoint
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" $SERVICE_URL/health
```

## ⚠️ Common Issues

### Issue 1: "Permission denied" on scripts
```bash
# Solution:
chmod +x setup.sh deploy.sh local_dev.sh
```

### Issue 2: "Project not found"
```bash
# Solution: Verify project ID
gcloud projects list
# Update config files with correct project ID
```

### Issue 3: "API not enabled"
```bash
# Solution: Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Issue 4: "Secret not found"
```bash
# Solution: Verify secret was created
gcloud secrets list --project=$PROJECT_ID

# Recreate if needed
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create lexguard-gemini-api-key \
    --data-file=- \
    --project=$PROJECT_ID
```

### Issue 5: "Service account not found"
```bash
# Solution: Verify service account exists
gcloud iam service-accounts list --project=$PROJECT_ID

# Recreate if needed
gcloud iam service-accounts create svc-lexguard-backend \
    --display-name="LexGuard Backend Service Account" \
    --project=$PROJECT_ID
```

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Service is running: `gcloud run services list --region=$REGION`
- [ ] Health check passes: `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SERVICE_URL/health`
- [ ] Logs are clean: `gcloud run services logs read lexguard-backend --region=$REGION --limit=20`
- [ ] No secrets in logs: Check logs don't contain API keys
- [ ] Service account is correct: `gcloud run services describe lexguard-backend --region=$REGION --format='value(spec.template.spec.serviceAccountName)'`
- [ ] Ingress is internal: `gcloud run services describe lexguard-backend --region=$REGION --format='value(spec.template.metadata.annotations.run\.googleapis\.com/ingress)'`

## 📊 Post-Deployment

### 1. Set Up Monitoring
```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# View metrics
echo "https://console.cloud.google.com/run/detail/$REGION/lexguard-backend/metrics?project=$PROJECT_ID"
```

### 2. Set Up Alerts
```bash
# Create notification channel
gcloud alpha monitoring channels create \
    --display-name="LexGuard Alerts" \
    --type=email \
    --channel-labels=email_address=your-email@example.com
```

### 3. Test with Real Data
```bash
# Run test suite
python test_api.py
```

### 4. Configure Authentication
See DEPLOYMENT.md for:
- Cloud Load Balancer with IAP setup
- Service-to-service authentication
- Custom domain configuration

## 📚 Next Steps

1. **Review Documentation**
   - [ ] Read ARCHITECTURE.md for system design
   - [ ] Read SECURITY.md for security best practices
   - [ ] Read DEPLOYMENT.md for advanced configuration

2. **Customize Agents**
   - [ ] Review agent prompts in agents/*.py
   - [ ] Adjust for your specific use case
   - [ ] Test with sample clauses

3. **Set Up CI/CD**
   - [ ] Configure GitHub Actions or Cloud Build triggers
   - [ ] Set up staging environment
   - [ ] Implement automated testing

4. **Scale for Production**
   - [ ] Adjust Cloud Run scaling settings
   - [ ] Set up multi-region deployment
   - [ ] Configure Cloud Armor for DDoS protection
   - [ ] Implement rate limiting

## ✅ Final Checklist

Before going to production:

- [ ] All TODO comments in code replaced
- [ ] Gemini API key stored in Secret Manager
- [ ] Service account has minimal permissions only
- [ ] Firestore initialized
- [ ] No secrets in git repository
- [ ] .gitignore includes all sensitive patterns
- [ ] --no-allow-unauthenticated is set
- [ ] Ingress is internal-and-cloud-load-balancing
- [ ] Monitoring and alerts configured
- [ ] Tested with real contract clauses
- [ ] Documentation reviewed
- [ ] Team trained on system

## 🎉 You're Ready!

Once all items are checked, you're ready to deploy LexGuard RiskScope to production!

For support, refer to:
- QUICKSTART.md - Quick deployment guide
- DEPLOYMENT.md - Detailed procedures
- SECURITY.md - Security guidelines
- ARCHITECTURE.md - System design

Good luck! 🚀
