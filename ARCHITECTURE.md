# LexGuard RiskScope Architecture

## System Overview

LexGuard RiskScope is a contract intelligence platform that analyzes legal clauses using a 4-agent AI pipeline powered by Gemini 1.5 Pro.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Application                        │
│                    (Frontend/Pipeline Service)                   │
└────────────┬────────────────────────────────────┬────────────────┘
             │                                    │
             │ POST /api/pipeline/ingest          │ WS /ws/{job_id}
             │ GET  /api/analyze/{job_id}         │ (Real-time events)
             │ GET  /api/report/{job_id}          │
             │                                    │
┌────────────▼────────────────────────────────────▼────────────────┐
│                      Cloud Load Balancer                         │
│                    (with IAP Authentication)                     │
└────────────┬─────────────────────────────────────────────────────┘
             │
             │ HTTPS (TLS 1.2+)
             │
┌────────────▼─────────────────────────────────────────────────────┐
│                         Cloud Run Service                         │
│                    lexguard-backend (FastAPI)                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                      main.py                             │    │
│  │  • POST /api/pipeline/ingest  → Create job              │    │
│  │  • GET  /api/analyze/{job_id} → Trigger analysis        │    │
│  │  • WS   /ws/{job_id}          → Stream events           │    │
│  │  • GET  /api/report/{job_id}  → Return results          │    │
│  └────────────┬────────────────────────────────────────────┘    │
│               │                                                   │
│  ┌────────────▼────────────────────────────────────────────┐    │
│  │                  orchestrator.py                         │    │
│  │         4-Agent Sequential Pipeline                      │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  1. Extractor Agent (agents/extractor.py)        │  │    │
│  │  │     • Classifies clause type                     │  │    │
│  │  │     • Types: non-compete, IP-transfer, etc.      │  │    │
│  │  └──────────────────┬───────────────────────────────┘  │    │
│  │                     │                                   │    │
│  │  ┌──────────────────▼───────────────────────────────┐  │    │
│  │  │  2. Analyst Agent (agents/analyst.py)            │  │    │
│  │  │     • Scores 5 risk dimensions (0-10)            │  │    │
│  │  │     • financial, privacy, IP, employment, etc.   │  │    │
│  │  └──────────────────┬───────────────────────────────┘  │    │
│  │                     │                                   │    │
│  │  ┌──────────────────▼───────────────────────────────┐  │    │
│  │  │  3. Adversary Agent (agents/adversary.py) ★USP   │  │    │
│  │  │     • Hostile lawyer perspective                 │  │    │
│  │  │     • How clause could be weaponized             │  │    │
│  │  │     • Specific legal outcomes                    │  │    │
│  │  └──────────────────┬───────────────────────────────┘  │    │
│  │                     │                                   │    │
│  │  ┌──────────────────▼───────────────────────────────┐  │    │
│  │  │  4. Advisor Agent (agents/advisor.py)            │  │    │
│  │  │     • Plain language summary                     │  │    │
│  │  │     • Severity rating                            │  │    │
│  │  │     • Negotiation recommendations                │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Service Account: svc-lexguard-backend                           │
│  • secretmanager.secretAccessor                                  │
│  • datastore.user                                                │
│  • run.invoker                                                   │
└───────────┬──────────────────┬──────────────────┬────────────────┘
            │                  │                  │
            │                  │                  │
┌───────────▼────────┐ ┌───────▼────────┐ ┌──────▼──────────┐
│  Secret Manager    │ │   Firestore    │ │  Gemini 1.5 Pro │
│                    │ │                │ │                 │
│ • Gemini API Key   │ │ • Job metadata │ │ • All LLM calls │
│ • Runtime access   │ │ • Clause data  │ │ • Classification│
│ • No hardcoded     │ │ • Analysis     │ │ • Risk scoring  │
│   secrets          │ │   results      │ │ • Adversarial   │
│                    │ │                │ │   analysis      │
└────────────────────┘ └────────────────┘ └─────────────────┘
```

## Component Details

### 1. FastAPI Application (main.py)

**Responsibilities:**
- HTTP endpoint handling
- WebSocket connection management
- Background task orchestration
- Request validation via Pydantic

**Key Features:**
- Async/await for concurrent operations
- WebSocket streaming for real-time updates
- Background task processing
- Health check endpoint for Cloud Run

### 2. Orchestrator (orchestrator.py)

**Responsibilities:**
- Sequential agent execution
- Event emission for WebSocket clients
- Error handling and recovery
- Result aggregation

**Flow:**
```
For each clause:
  1. Run Extractor → emit event
  2. Run Analyst → emit event
  3. Run Adversary → emit event
  4. Run Advisor → emit event
  5. Store result → emit complete event
```

### 3. Agent Pipeline

#### Extractor Agent
- **Input:** Clause text
- **Output:** Clause type (8 categories)
- **Model:** Gemini 1.5 Pro
- **Prompt:** Classification with predefined categories

#### Analyst Agent
- **Input:** Clause text + type
- **Output:** RiskScores (5 dimensions, 0-10 scale)
- **Model:** Gemini 1.5 Pro
- **Prompt:** Structured JSON scoring

#### Adversary Agent ★ THE USP
- **Input:** Clause text + type
- **Output:** Adversarial argument (text)
- **Model:** Gemini 1.5 Pro
- **Prompt:** "You are a hostile lawyer..."
- **Unique Value:** Shows worst-case weaponization

#### Advisor Agent
- **Input:** All previous outputs
- **Output:** Summary + severity + recommendations
- **Model:** Gemini 1.5 Pro
- **Prompt:** Synthesis and actionable advice

### 4. Storage Layer (storage.py)

**Firestore Collections:**
```
analysis_jobs/
  {job_id}/
    - job_id: string
    - status: "pending" | "processing" | "completed" | "failed"
    - total_clauses: int
    - processed_clauses: int
    - clauses: array[Clause]
    - analyses: array[ClauseAnalysis]
```

**Operations:**
- `create_job()` - Initialize new analysis job
- `update_job_status()` - Update processing status
- `add_clause_analysis()` - Store completed analysis
- `get_job()` - Retrieve full report

### 5. Configuration (config.py)

**Secret Management:**
- Runtime retrieval from Secret Manager
- LRU cache for performance
- No secrets in environment variables
- No secrets in logs

## Data Flow

### Ingestion Flow
```
1. Client → POST /api/pipeline/ingest
   {
     "job_id": "job-123",
     "clauses": [...]
   }

2. FastAPI validates request (Pydantic)

3. Storage creates job in Firestore
   - Status: "pending"
   - Stores clauses array

4. Response: 200 OK
   {
     "status": "success",
     "job_id": "job-123",
     "total_clauses": 10
   }
```

### Analysis Flow
```
1. Client → GET /api/analyze/{job_id}

2. FastAPI starts background task

3. Background task:
   a. Update status → "processing"
   b. For each clause:
      - Run 4-agent pipeline
      - Emit WebSocket events
      - Store result in Firestore
   c. Update status → "completed"

4. Immediate response: 200 OK
   {
     "status": "started",
     "message": "Connect to /ws/{job_id}"
   }
```

### WebSocket Flow
```
1. Client → WS /ws/{job_id}

2. Connection established

3. Events streamed:
   - started
   - extractor_complete
   - analyst_complete
   - adversary_complete
   - advisor_complete
   - clause_complete
   - job_complete

4. Each event:
   {
     "event": "analyst_complete",
     "clause_id": "clause-1",
     "data": {
       "risk_scores": {...}
     }
   }
```

### Report Retrieval Flow
```
1. Client → GET /api/report/{job_id}

2. Storage retrieves from Firestore

3. Response: 200 OK
   {
     "job_id": "job-123",
     "status": "completed",
     "clauses": [
       {
         "clause_id": "...",
         "clause_type": "...",
         "risk_scores": {...},
         "adversary_argument": "...",
         "plain_language_summary": "...",
         "severity": "high",
         "negotiation_recommendation": "..."
       }
     ],
     "total_clauses": 10,
     "processed_clauses": 10
   }
```

## Security Architecture

### Defense in Depth

**Layer 1: Network**
- Cloud Load Balancer with IAP
- Internal ingress only
- TLS 1.2+ encryption

**Layer 2: Authentication**
- No unauthenticated access
- Service account with minimal permissions
- IAM-based authorization

**Layer 3: Application**
- Input validation (Pydantic)
- No SQL injection (Firestore NoSQL)
- Error messages don't expose internals

**Layer 4: Data**
- Secrets in Secret Manager
- Firestore encryption at rest
- No PII in logs

**Layer 5: Container**
- Non-root user (UID 1000)
- Minimal base image
- Vulnerability scanning

## Scalability

### Horizontal Scaling
- Cloud Run auto-scales based on requests
- Max instances: 100 (configurable)
- Concurrent requests per instance: 80

### Performance Characteristics
- **Ingestion:** ~50ms (Firestore write)
- **Analysis trigger:** ~100ms (background task start)
- **Per-clause analysis:** ~10-15 seconds (4 Gemini calls)
- **WebSocket latency:** <100ms per event

### Bottlenecks
1. **Gemini API rate limits** - Primary constraint
2. **Firestore writes** - Transactional updates
3. **WebSocket connections** - Memory per connection

### Optimization Strategies
- Batch Gemini calls where possible
- Cache common clause classifications
- Connection pooling for Firestore
- Async/await for I/O operations

## Monitoring & Observability

### Metrics
- Request count and latency
- Error rates by endpoint
- Gemini API call duration
- Firestore operation latency
- WebSocket connection count

### Logs
- Structured JSON logging
- Cloud Logging integration
- No sensitive data in logs
- Error stack traces

### Alerts
- High error rate (>5%)
- Slow response time (>30s)
- Failed Gemini API calls
- Firestore quota exceeded

## Cost Estimation

### Per 1000 Clauses Analyzed

**Gemini API:**
- 4 calls per clause × 1000 clauses = 4000 calls
- ~500 tokens per call = 2M tokens
- Cost: ~$7 (input) + ~$21 (output) = **$28**

**Cloud Run:**
- ~15 seconds per clause × 1000 = 4.17 hours
- 2 vCPU, 2GB RAM
- Cost: **~$1**

**Firestore:**
- 1000 writes + 1000 reads
- Cost: **~$0.50**

**Total: ~$30 per 1000 clauses**

## Deployment Topology

### Development
```
Single region: us-central1
Min instances: 0
Max instances: 5
Resources: 1 vCPU, 1GB RAM
```

### Production
```
Multi-region: us-central1, us-east1
Min instances: 2 per region
Max instances: 100 per region
Resources: 2 vCPU, 2GB RAM
Load balancer: Global
```

## Disaster Recovery

### Backup Strategy
- Firestore: Automatic daily backups
- Secrets: Versioned in Secret Manager
- Code: Git repository

### Recovery Time Objective (RTO)
- Service failure: <5 minutes (Cloud Run auto-restart)
- Region failure: <15 minutes (multi-region failover)
- Data loss: <24 hours (Firestore backup)

### Recovery Point Objective (RPO)
- In-progress analyses: May need re-run
- Completed analyses: Zero data loss (Firestore)

## Future Enhancements

### Phase 2
- [ ] Batch analysis API
- [ ] Clause comparison feature
- [ ] Custom risk weights
- [ ] Multi-language support

### Phase 3
- [ ] ML-based clause extraction from PDFs
- [ ] Historical risk trend analysis
- [ ] Integration with DocuSign
- [ ] White-label deployment

### Phase 4
- [ ] Fine-tuned models for specific industries
- [ ] Automated negotiation suggestions
- [ ] Contract template library
- [ ] Collaborative review features
