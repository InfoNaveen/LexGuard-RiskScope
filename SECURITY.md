# Security Guidelines for LexGuard RiskScope Backend

## Security Architecture

### 1. Secret Management
- **All secrets stored in GCP Secret Manager**
- No hardcoded API keys or credentials
- Runtime secret retrieval only
- Secrets never logged or exposed in responses

### 2. IAM & Service Accounts
- Dedicated service account: `svc-lexguard-backend`
- Minimal permissions (principle of least privilege):
  - `secretmanager.secretAccessor` - Read secrets only
  - `datastore.user` - Firestore read/write
  - `run.invoker` - Cloud Run invocation
- No owner or editor roles

### 3. Network Security
- Cloud Run ingress: `internal-and-cloud-load-balancing`
- No public unauthenticated access (`--no-allow-unauthenticated`)
- Must use Cloud Load Balancer or VPC for access
- WebSocket connections authenticated via same mechanism

### 4. Container Security
- Non-root user (UID 1000)
- Python 3.12 slim base image (minimal attack surface)
- No secrets in image layers
- Automated vulnerability scanning in CI/CD
- `.dockerignore` prevents sensitive files in image

### 5. Data Security
- Firestore with IAM-based access control
- No PII logged
- Clause data encrypted at rest (Firestore default)
- Encrypted in transit (TLS 1.2+)

### 6. Application Security
- Input validation via Pydantic models
- No SQL injection risk (Firestore NoSQL)
- Rate limiting via Cloud Run concurrency settings
- Error messages don't expose internal details

## Security Checklist

### Before Deployment
- [ ] All TODO comments in code replaced with actual values
- [ ] Gemini API key stored in Secret Manager
- [ ] Service account created with minimal permissions
- [ ] Firestore initialized with proper IAM rules
- [ ] No `.env` files or credentials in repository
- [ ] `.gitignore` includes all sensitive patterns

### After Deployment
- [ ] Verify `--no-allow-unauthenticated` is set
- [ ] Test that unauthenticated requests are rejected
- [ ] Verify service account has only required roles
- [ ] Check Cloud Run logs for any secret leakage
- [ ] Enable Cloud Armor for DDoS protection (optional)
- [ ] Set up Cloud Monitoring alerts

## Incident Response

### If API Key is Compromised
1. Immediately revoke the compromised key in Gemini console
2. Generate new API key
3. Update Secret Manager with new key
4. Redeploy service (Cloud Run will pick up new secret)
5. Review Cloud Run logs for unauthorized usage

### If Service Account is Compromised
1. Disable the service account immediately
2. Create new service account with same permissions
3. Update Cloud Run service to use new service account
4. Review audit logs for unauthorized actions
5. Rotate all secrets the account had access to

## Compliance Notes

- **GDPR**: Clause text may contain PII - ensure data retention policies
- **SOC 2**: Audit logs enabled via Cloud Logging
- **HIPAA**: Not HIPAA-compliant by default - requires BAA with GCP
- **Data Residency**: Firestore and Cloud Run region must match requirements

## Security Contacts

For security issues, contact: security@lexguard.example.com

## Regular Security Tasks

### Weekly
- Review Cloud Run access logs
- Check for failed authentication attempts
- Monitor Secret Manager access logs

### Monthly
- Review IAM permissions
- Update dependencies (`pip list --outdated`)
- Review Firestore access patterns

### Quarterly
- Rotate Gemini API key
- Security audit of codebase
- Penetration testing
- Review and update this document

## Known Limitations

1. **WebSocket Authentication**: Currently relies on Cloud Run authentication. Consider adding JWT tokens for additional security.

2. **Rate Limiting**: Cloud Run provides basic rate limiting. For production, add application-level rate limiting per job_id.

3. **Input Sanitization**: Clause text is passed directly to Gemini. Consider adding content filtering for malicious prompts.

4. **Audit Logging**: Basic Cloud Logging enabled. Consider structured audit logs for compliance.

## Secure Development Practices

### Code Review Requirements
- No hardcoded secrets
- All external inputs validated
- Error handling doesn't expose internals
- Logging doesn't include sensitive data

### Testing
- Test with malicious inputs
- Verify authentication on all endpoints
- Test secret rotation scenarios
- Validate IAM permissions

### Dependencies
- Pin all versions in `requirements.txt`
- Regular security updates
- Scan for known vulnerabilities
- Use official packages only
