"""Analyst Agent - Scores clauses on 5 risk axes."""
import json
import google.generativeai as genai
from config import get_gemini_api_key
from models import RiskScores


class AnalystAgent:
    """Analyzes clauses and scores them on multiple risk dimensions."""
    
    def __init__(self):
        """Initialize the analyst agent with Gemini."""
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def analyze_risks(self, clause_text: str, clause_type: str) -> RiskScores:
        """
        Score a clause on 5 risk axes from 0-10.
        
        Args:
            clause_text: The text of the clause to analyze
            clause_type: The classified type of the clause
            
        Returns:
            RiskScores object with scores for each risk dimension
        """
        prompt = f"""You are a legal risk analyst. Analyze the following contract clause and score it on 5 risk dimensions from 0 to 10, where:
- 0 = No risk / Highly favorable
- 5 = Moderate risk / Standard terms
- 10 = Extreme risk / Highly unfavorable

Clause Type: {clause_type}

Clause Text:
{clause_text}

Score these 5 dimensions:
1. financial_risk: Direct monetary impact, penalties, fees, payment obligations
2. privacy_risk: Data collection, sharing, privacy violations, surveillance
3. ip_risk: Loss of intellectual property rights, patent claims, copyright transfer
4. employment_risk: Job security, non-compete restrictions, termination ease
5. compliance_risk: Regulatory violations, legal liability, audit requirements

Respond with ONLY a valid JSON object in this exact format:
{{
  "financial_risk": <0-10>,
  "privacy_risk": <0-10>,
  "ip_risk": <0-10>,
  "employment_risk": <0-10>,
  "compliance_risk": <0-10>
}}"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            scores_dict = json.loads(response_text)
            
            # Validate and clamp scores to 0-10 range
            for key in scores_dict:
                scores_dict[key] = max(0, min(10, int(scores_dict[key])))
            
            return RiskScores(**scores_dict)
            
        except Exception as e:
            print(f"Error in risk analysis: {type(e).__name__}")
            # Return moderate risk scores as fallback
            return RiskScores(
                financial_risk=5,
                privacy_risk=5,
                ip_risk=5,
                employment_risk=5,
                compliance_risk=5
            )
