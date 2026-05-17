# LexGuard RiskScope - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Prerequisites
- GCP account with billing
- `gcloud` CLI installed
- Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Step 1: Clone & Configure (1 min)

```bash
# Set your values
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export GEMINI_KEY="your-gemini-api-key"

# Update config files
sed -i "s/YOUR_PROJECT_ID/$PROJECT_ID/g" config.py cloudbuild.yaml setup.sh deploy.sh
sed -i "s/YOUR_REGION/$REGION/g" cloudbuild.yaml deploy.sh
```

### Step 2: Run Setup (2 min)

```bash
chmod +x setup.sh
./setup.sh
# When prompted, paste your Gemini API key
```

This creates:
- ✅ Service account with minimal permissions
- ✅ Firestore database
- ✅ Secret Manager secret for API key
- ✅ All IAM bindings

### Step 3: Deploy (2 min)

```bash
chmod +x deploy.sh
./deploy.sh
```

This:
- ✅ Builds Docker container
- ✅ Runs vulnerability scan
- ✅ Deploys to Cloud Run
- ✅ Outputs service URL

### Step 4: Test

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe lexguard-backend \
    --region=$REGION \
    --format='value(status.url)')

# Test with authentication
TOKEN=$(gcloud auth print-identity-token)

# Health check
curl -H "Authorization: Bearer $TOKEN" $SERVICE_URL/health

# Ingest test clause
curl -X POST $SERVICE_URL/api/pipeline/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test-001",
    "clauses": [{
      "clause_id": "c1",
      "text": "Employee agrees not to compete with Company for 2 years after termination within 50 miles of any office."
    }]
  }'

# Start analysis
curl -H "Authorization: Bearer $TOKEN" \
  $SERVICE_URL/api/analyze/test-001

# Wait 30 seconds, then get report
sleep 30
curl -H "Authorization: Bearer $TOKEN" \
  $SERVICE_URL/api/report/test-001
```

## 📁 Project Structure

```
lexguard-backend/
├── main.py                 # FastAPI app with 4 endpoints
├── orchestrator.py         # 4-agent pipeline coordinator
├── agents/
│   ├── extractor.py       # Clause classification
│   ├── analyst.py         # Risk scoring (5 axes)
│   ├── adversary.py       # Hostile interpretation ★USP
│   └── advisor.py         # Recommendations
├── models.py              # Pydantic schemas
├── storage.py             # Firestore operations
├── config.py              # Secret Manager integration
├── Dockerfile             # Container definition
├── cloudbuild.yaml        # GCP deployment config
└── requirements.txt       # Python dependencies
```

## 🔑 Key Features

### 1. Four Exact API Endpoints
- `POST /api/pipeline/ingest` - Receive clauses
- `GET /api/analyze/{job_id}` - Trigger analysis
- `WS /ws/{job_id}` - Real-time streaming
- `GET /api/report/{job_id}` - Download results

### 2. Four-Agent Pipeline
1. **Extractor** → Classifies clause type
2. **Analyst** → Scores 5 risk dimensions (0-10)
3. **Adversary** → Hostile lawyer perspective ★THE USP
4. **Advisor** → Plain language + recommendations

### 3. Security Built-In
- ✅ No hardcoded secrets (Secret Manager)
- ✅ Non-root container user
- ✅ No unauthenticated access
- ✅ Internal ingress only
- ✅ Vulnerability scanning
- ✅ Minimal IAM permissions

## 🔧 Local Development

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set project ID
export GCP_PROJECT_ID=$PROJECT_ID

# Authenticate with GCP
gcloud auth application-default login

# Run locally
uvicorn main:app --reload --port 8080

# Test locally
python test_api.py
```

## 📊 Example Response

```json
{
  "job_id": "test-001",
  "status": "completed",
  "clauses": [{
    "clause_id": "c1",
    "clause_text": "Employee agrees not to compete...",
    "clause_type": "non-compete",
    "risk_scores": {
      "financial_risk": 6,
      "privacy_risk": 2,
      "ip_risk": 3,
      "employment_risk": 9,
      "compliance_risk": 5
    },
    "adversary_argument": "This non-compete clause could be weaponized by arguing that any employment in the same industry constitutes competition, even in a non-competing role. The 50-mile radius could encompass major metropolitan areas, effectively barring employment. Courts in this jurisdiction have upheld similar clauses, and the 2-year period exceeds typical reasonableness standards, potentially extending to related industries through broad interpretation of 'compete'...",
    "plain_language_summary": "You cannot work for any competing company within 50 miles of any company office for 2 years after leaving. This is a very restrictive non-compete agreement.",
    "severity": "high",
    "negotiation_recommendation": "Request to narrow the definition of 'compete' to direct competitors only, reduce the time period to 6-12 months, and limit the geographic scope to the specific office location where you worked. Consider requesting a buyout clause that allows you to pay a fee to exit the restriction early."
  }],
  "total_clauses": 1,
  "processed_clauses": 1
}
```

## 🎯 What Makes This Special

### The Adversary Agent (THE USP)
Unlike other contract analysis tools that just highlight risks, LexGuard shows you **exactly how a hostile lawyer would weaponize each clause against you**. This is the unique selling point:

```
System Prompt: "You are a hostile lawyer hired by the counterparty. 
Argue how this clause could be weaponized against the user in the 
worst realistic scenario. Be specific, cite realistic legal outcomes."
```

This gives users unprecedented insight into contract vulnerabilities.

## 💰 Cost Estimate

Per 1000 clauses analyzed:
- Gemini API: ~$28
- Cloud Run: ~$1
- Firestore: ~$0.50
- **Total: ~$30**

## 📚 Documentation

- **README.md** - Overview and setup
- **ARCHITECTURE.md** - System design and data flow
- **DEPLOYMENT.md** - Detailed deployment guide
- **SECURITY.md** - Security guidelines
- **openapi.yaml** - API specification

## 🆘 Troubleshooting

### "Permission denied" errors
```bash
# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:svc-lexguard-backend"
```

### "Secret not found" errors
```bash
# Verify secret exists
gcloud secrets describe lexguard-gemini-api-key --project=$PROJECT_ID

# Recreate if needed
echo -n "$GEMINI_KEY" | gcloud secrets create lexguard-gemini-api-key \
  --data-file=- --project=$PROJECT_ID
```

### Service won't start
```bash
# Check logs
gcloud run services logs read lexguard-backend --region=$REGION --limit=50
```

## 🔄 Next Steps

1. **Set up authentication** - Configure Cloud Load Balancer with IAP
2. **Enable monitoring** - Set up Cloud Monitoring alerts
3. **Test at scale** - Run load tests with multiple concurrent jobs
4. **Customize agents** - Adjust prompts for your specific use case
5. **Add features** - Implement batch processing, caching, etc.

## 📞 Support

- Check logs: `gcloud run services logs tail lexguard-backend --region=$REGION`
- Review SECURITY.md for security best practices
- See DEPLOYMENT.md for advanced configuration

---

**Built with:** Python 3.12 • FastAPI • Gemini 1.5 Pro • GCP Cloud Run • Firestore
