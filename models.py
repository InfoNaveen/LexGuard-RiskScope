"""Pydantic models for LexGuard RiskScope API."""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Clause(BaseModel):
    """Individual contract clause."""
    clause_id: str
    text: str
    page_number: Optional[int] = None


class IngestRequest(BaseModel):
    """Request body for /api/pipeline/ingest endpoint."""
    job_id: str
    clauses: List[Clause]


class RiskScores(BaseModel):
    """Risk scores from analyst agent."""
    financial_risk: int = Field(ge=0, le=10)
    privacy_risk: int = Field(ge=0, le=10)
    ip_risk: int = Field(ge=0, le=10)
    employment_risk: int = Field(ge=0, le=10)
    compliance_risk: int = Field(ge=0, le=10)


class ClauseAnalysis(BaseModel):
    """Complete analysis result for a single clause."""
    clause_id: str
    clause_text: str
    clause_type: str
    risk_scores: RiskScores
    adversary_argument: str
    plain_language_summary: str
    severity: Literal["critical", "high", "medium", "low"]
    negotiation_recommendation: str


class AnalysisReport(BaseModel):
    """Full analysis report for a job."""
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    clauses: List[ClauseAnalysis]
    total_clauses: int
    processed_clauses: int


class WebSocketEvent(BaseModel):
    """WebSocket event structure."""
    event: Literal["started", "extractor_complete", "analyst_complete", 
                   "adversary_complete", "advisor_complete", "clause_complete", 
                   "job_complete", "error"]
    clause_id: Optional[str] = None
    data: Optional[dict] = None
