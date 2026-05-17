"""Orchestrator - Runs all 4 agents sequentially and emits WebSocket events."""
import asyncio
from typing import Optional, Callable, Dict, Any
from models import Clause, ClauseAnalysis, RiskScores
from agents.extractor import ExtractorAgent
from agents.analyst import AnalystAgent
from agents.adversary import AdversaryAgent
from agents.advisor import AdvisorAgent


class Orchestrator:
    """Orchestrates the 4-agent pipeline for clause analysis."""
    
    def __init__(self):
        """Initialize all agents."""
        self.extractor = ExtractorAgent()
        self.analyst = AnalystAgent()
        self.adversary = AdversaryAgent()
        self.advisor = AdvisorAgent()
    
    async def analyze_clause(
        self,
        clause: Clause,
        event_callback: Optional[Callable[[str, str, Dict[str, Any]], None]] = None
    ) -> ClauseAnalysis:
        """
        Run all 4 agents sequentially on a single clause.
        
        Args:
            clause: The clause to analyze
            event_callback: Optional callback for WebSocket events
                           Signature: callback(event_type, clause_id, data)
        
        Returns:
            Complete ClauseAnalysis object
        """
        clause_id = clause.clause_id
        
        # Emit started event
        if event_callback:
            await event_callback("started", clause_id, {"clause_text": clause.text})
        
        try:
            # Step 1: Extract clause type
            clause_type = await asyncio.to_thread(
                self.extractor.classify_clause,
                clause.text
            )
            
            if event_callback:
                await event_callback("extractor_complete", clause_id, {
                    "clause_type": clause_type
                })
            
            # Step 2: Analyze risks
            risk_scores = await asyncio.to_thread(
                self.analyst.analyze_risks,
                clause.text,
                clause_type
            )
            
            if event_callback:
                await event_callback("analyst_complete", clause_id, {
                    "risk_scores": risk_scores.model_dump()
                })
            
            # Step 3: Generate adversary argument (THE USP)
            adversary_argument = await asyncio.to_thread(
                self.adversary.generate_adversary_argument,
                clause.text,
                clause_type
            )
            
            if event_callback:
                await event_callback("adversary_complete", clause_id, {
                    "adversary_argument": adversary_argument
                })
            
            # Step 4: Generate advice
            plain_language_summary, severity, negotiation_recommendation = await asyncio.to_thread(
                self.advisor.generate_advice,
                clause.text,
                clause_type,
                risk_scores,
                adversary_argument
            )
            
            if event_callback:
                await event_callback("advisor_complete", clause_id, {
                    "plain_language_summary": plain_language_summary,
                    "severity": severity,
                    "negotiation_recommendation": negotiation_recommendation
                })
            
            # Build complete analysis
            analysis = ClauseAnalysis(
                clause_id=clause_id,
                clause_text=clause.text,
                clause_type=clause_type,
                risk_scores=risk_scores,
                adversary_argument=adversary_argument,
                plain_language_summary=plain_language_summary,
                severity=severity,
                negotiation_recommendation=negotiation_recommendation
            )
            
            if event_callback:
                await event_callback("clause_complete", clause_id, {
                    "analysis": analysis.model_dump()
                })
            
            return analysis
            
        except Exception as e:
            error_msg = f"Error analyzing clause: {type(e).__name__}"
            print(error_msg)
            
            if event_callback:
                await event_callback("error", clause_id, {
                    "error": error_msg
                })
            
            raise
    
    async def analyze_job(
        self,
        clauses: list[Clause],
        event_callback: Optional[Callable[[str, str, Dict[str, Any]], None]] = None
    ) -> list[ClauseAnalysis]:
        """
        Analyze all clauses in a job sequentially.
        
        Args:
            clauses: List of clauses to analyze
            event_callback: Optional callback for WebSocket events
        
        Returns:
            List of ClauseAnalysis objects
        """
        results = []
        
        for clause in clauses:
            analysis = await self.analyze_clause(clause, event_callback)
            results.append(analysis)
        
        return results
