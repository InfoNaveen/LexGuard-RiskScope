"""Advisor Agent - Synthesizes analysis into actionable recommendations."""
import json
import google.generativeai as genai
from config import get_gemini_api_key
from models import RiskScores
from typing import Tuple, Literal


class AdvisorAgent:
    """Synthesizes all analysis into plain language summary and recommendations."""
    
    def __init__(self):
        """Initialize the advisor agent with Gemini."""
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def generate_advice(
        self,
        clause_text: str,
        clause_type: str,
        risk_scores: RiskScores,
        adversary_argument: str
    ) -> Tuple[str, Literal["critical", "high", "medium", "low"], str]:
        """
        Generate plain language summary, severity, and negotiation recommendation.
        
        Args:
            clause_text: The text of the clause
            clause_type: The classified type
            risk_scores: Risk scores from analyst
            adversary_argument: Adversarial interpretation
            
        Returns:
            Tuple of (plain_language_summary, severity, negotiation_recommendation)
        """
        prompt = f"""You are a trusted legal advisor helping a client understand a contract clause. You have access to:

1. The clause itself
2. Risk scores from analysis
3. An adversarial interpretation from opposing counsel

Your job: Provide clear, actionable advice.

Clause Type: {clause_type}

Clause Text:
{clause_text}

Risk Scores (0-10 scale):
- Financial Risk: {risk_scores.financial_risk}
- Privacy Risk: {risk_scores.privacy_risk}
- IP Risk: {risk_scores.ip_risk}
- Employment Risk: {risk_scores.employment_risk}
- Compliance Risk: {risk_scores.compliance_risk}

Adversarial Interpretation:
{adversary_argument}

Provide your response as a JSON object with these three fields:

1. plain_language_summary: Explain what this clause means in simple terms (2-3 sentences)
2. severity: Rate as "critical", "high", "medium", or "low" based on overall risk
3. negotiation_recommendation: Specific, actionable advice on how to negotiate this clause (3-4 sentences)

Respond with ONLY valid JSON in this exact format:
{{
  "plain_language_summary": "...",
  "severity": "critical|high|medium|low",
  "negotiation_recommendation": "..."
}}"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            advice_dict = json.loads(response_text)
            
            # Validate severity
            severity = advice_dict.get("severity", "medium").lower()
            if severity not in ["critical", "high", "medium", "low"]:
                severity = "medium"
            
            return (
                advice_dict.get("plain_language_summary", "Summary unavailable"),
                severity,
                advice_dict.get("negotiation_recommendation", "Consult with legal counsel")
            )
            
        except Exception as e:
            print(f"Error in advisor analysis: {type(e).__name__}")
            # Calculate severity from risk scores as fallback
            avg_risk = (
                risk_scores.financial_risk +
                risk_scores.privacy_risk +
                risk_scores.ip_risk +
                risk_scores.employment_risk +
                risk_scores.compliance_risk
            ) / 5
            
            if avg_risk >= 8:
                severity = "critical"
            elif avg_risk >= 6:
                severity = "high"
            elif avg_risk >= 4:
                severity = "medium"
            else:
                severity = "low"
            
            return (
                f"This is a {clause_type} clause. Technical error prevented detailed analysis.",
                severity,
                "Consult with legal counsel for detailed review of this clause."
            )
