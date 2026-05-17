"""Firestore storage layer for clause analysis results."""
from google.cloud import firestore
from typing import Optional, List
from models import AnalysisReport, ClauseAnalysis, Clause


class FirestoreStorage:
    """Manages storage of analysis results in Firestore."""
    
    def __init__(self):
        """Initialize Firestore client."""
        self.db = firestore.Client()
        self.jobs_collection = "analysis_jobs"
    
    def create_job(self, job_id: str, clauses: List[Clause]) -> None:
        """
        Create a new analysis job in Firestore.
        
        Args:
            job_id: Unique job identifier
            clauses: List of clauses to analyze
        """
        job_ref = self.db.collection(self.jobs_collection).document(job_id)
        job_ref.set({
            "job_id": job_id,
            "status": "pending",
            "total_clauses": len(clauses),
            "processed_clauses": 0,
            "clauses": [clause.model_dump() for clause in clauses],
            "analyses": []
        })
    
    def update_job_status(self, job_id: str, status: str) -> None:
        """
        Update job status.
        
        Args:
            job_id: Job identifier
            status: New status (pending, processing, completed, failed)
        """
        job_ref = self.db.collection(self.jobs_collection).document(job_id)
        job_ref.update({"status": status})
    
    def add_clause_analysis(self, job_id: str, analysis: ClauseAnalysis) -> None:
        """
        Add a completed clause analysis to the job.
        
        Args:
            job_id: Job identifier
            analysis: Completed clause analysis
        """
        job_ref = self.db.collection(self.jobs_collection).document(job_id)
        
        # Use transaction to safely update arrays
        @firestore.transactional
        def update_in_transaction(transaction, ref):
            snapshot = transaction.get(ref)
            current_analyses = snapshot.get("analyses") or []
            current_processed = snapshot.get("processed_clauses") or 0
            
            current_analyses.append(analysis.model_dump())
            
            transaction.update(ref, {
                "analyses": current_analyses,
                "processed_clauses": current_processed + 1
            })
        
        transaction = self.db.transaction()
        update_in_transaction(transaction, job_ref)
    
    def get_job(self, job_id: str) -> Optional[AnalysisReport]:
        """
        Retrieve a job and its analyses.
        
        Args:
            job_id: Job identifier
            
        Returns:
            AnalysisReport or None if not found
        """
        job_ref = self.db.collection(self.jobs_collection).document(job_id)
        doc = job_ref.get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # Convert analyses back to ClauseAnalysis objects
        analyses = [ClauseAnalysis(**analysis) for analysis in data.get("analyses", [])]
        
        return AnalysisReport(
            job_id=data["job_id"],
            status=data["status"],
            clauses=analyses,
            total_clauses=data["total_clauses"],
            processed_clauses=data["processed_clauses"]
        )
    
    def job_exists(self, job_id: str) -> bool:
        """
        Check if a job exists.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job exists, False otherwise
        """
        job_ref = self.db.collection(self.jobs_collection).document(job_id)
        return job_ref.get().exists
