# LexGuard RiskScope Backend

Contract intelligence platform with 4-agent orchestration powered by Gemini 1.5 Pro.

## Architecture

### Tech Stack
- **Python 3.12** with FastAPI and uvicorn
- **Gemini 1.5 Pro** for all LLM operations
- **Firestore** for clause storage
- **GCP Secret Manager** for secrets
- **Cloud Run** deployment target

### 4-Agent Pipeline

1. **Extractor Agent** (`agents/extractor.py`)
   - Classifies clauses: non-compete, IP-transfer, arbitration, termination, data-collection, liability, auto-renewal, other

2. **Analyst Agent** (`agents/analyst.py`)
   - Scores 0-10 on 5 axes: financial_risk, privacy_risk, ip_risk, employment_risk, compliance_risk

3. **Adversary Agent** (`agents/adversary.py`) - **THE USP**
   - Hostile lawyer perspective: argues how clause could be weaponized
   - Specific, realistic legal outcomes

4. **Advisor Agent** (`agents/advisor.py`)
   - Synthesizes: plain_language_summary, severity, negotiation_recommendation

## API Endpoints

### POST /api/pipeline/ingest
Receives job_id + clauses array from pipeline.

```json
{
  "job_id": "job-123",
  "clauses": [
    {
      "clause_id": "clause-1",
      "text": "Employee agrees not to compete...",
      "page_number": 5
    }
  ]
}
```

### GET /api/analyze/{job_id}
Triggers 4-agent chain, returns immediately, runs in background.

### WS /ws/{job_id}
WebSocket streaming events:
```json
{
  "event": "extractor_complete",
  "clause_id": "clause-1",
  "data": {"clause_type": "non-compete"}
}
```

### GET /api/report/{job_id}
Returns full JSON report for download.

## Setup

### Prerequisites
1. GCP project with billing enabled
2. APIs enabled:
   - Cloud Run
   - Firestore
   - Secret Manager
   - Container Registry

### 1. Create Service Account
```bash
# TODO: Replace YOUR_PROJECT_ID with actual project ID
gcloud iam service-accounts create svc-lexguard-backend \
  --display-name="LexGuard Backend Service Account" \
  --project=YOUR_PROJECT_ID

# Grant required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:svc-lexguard-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:svc-lexguard-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:svc-lexguard-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 2. Store Gemini API Key in Secret Manager
```bash
# TODO: Replace YOUR_GEMINI_API_KEY with actual key
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create lexguard-gemini-api-key \
  --data-file=- \
  --project=YOUR_PROJECT_ID
```

### 3. Initialize Firestore
```bash
gcloud firestore databases create --location=us-central1 --project=YOUR_PROJECT_ID
```

### 4. Update Configuration
Edit `config.py` and `cloudbuild.yaml`:
- Replace `YOUR_PROJECT_ID` with actual GCP project ID
- Replace `YOUR_REGION` with target region (e.g., us-central1)

### 5. Deploy
```bash
gcloud builds submit --config=cloudbuild.yaml --project=YOUR_PROJECT_ID
```

## Security Features

✅ **No hardcoded secrets** - All keys from Secret Manager  
✅ **Non-root container user** - Runs as UID 1000  
✅ **No unauthenticated access** - `--no-allow-unauthenticated`  
✅ **Internal ingress only** - `internal-and-cloud-load-balancing`  
✅ **Vulnerability scanning** - Automated in Cloud Build  
✅ **Minimal IAM permissions** - Principle of least privilege  

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export GCP_PROJECT_ID=YOUR_PROJECT_ID

# Run locally (requires GCP credentials)
uvicorn main:app --reload --port 8080
```

## Testing

```bash
# Ingest clauses
curl -X POST http://localhost:8080/api/pipeline/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test-job-1",
    "clauses": [
      {
        "clause_id": "clause-1",
        "text": "Employee agrees not to compete with Company for 2 years after termination."
      }
    ]
  }'

# Start analysis
curl http://localhost:8080/api/analyze/test-job-1

# Get report
curl http://localhost:8080/api/report/test-job-1
```

## Project Structure

```
.
├── main.py                 # FastAPI application
├── config.py              # Secret Manager integration
├── models.py              # Pydantic models
├── storage.py             # Firestore operations
├── orchestrator.py        # 4-agent pipeline
├── agents/
│   ├── extractor.py       # Clause classification
│   ├── analyst.py         # Risk scoring
│   ├── adversary.py       # Hostile interpretation (USP)
│   └── advisor.py         # Recommendations
├── Dockerfile             # Container definition
├── cloudbuild.yaml        # Cloud Build config
├── requirements.txt       # Python dependencies
├── openapi.yaml          # API specification
└── README.md             # This file
```

## License

Proprietary - LexGuard RiskScope
