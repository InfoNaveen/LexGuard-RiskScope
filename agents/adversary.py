"""Adversary Agent - THE USP: Hostile lawyer perspective."""
import google.generativeai as genai
from config import get_gemini_api_key


class AdversaryAgent:
    """
    Adversarial analysis agent - argues how clause could be weaponized.
    This is the unique selling point of LexGuard RiskScope.
    """
    
    def __init__(self):
        """Initialize the adversary agent with Gemini."""
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def generate_adversary_argument(self, clause_text: str, clause_type: str) -> str:
        """
        Generate hostile interpretation of how clause could be weaponized.
        
        Args:
            clause_text: The text of the clause to analyze
            clause_type: The classified type of the clause
            
        Returns:
            Adversary argument as string
        """
        system_prompt = """You are a hostile lawyer hired by the counterparty. Your job is to argue how this clause could be weaponized against the user in the worst realistic scenario. 

Be specific and cite realistic legal outcomes. Think like an aggressive opposing counsel looking for every possible advantage. Consider:
- Ambiguous language that could be interpreted against the user
- Hidden obligations or restrictions
- Worst-case enforcement scenarios
- Precedents that favor aggressive interpretation
- Procedural advantages for the counterparty
- Financial or operational leverage points

Be concrete, not hypothetical. Reference specific phrases in the clause and explain exactly how they could be exploited."""

        prompt = f"""{system_prompt}

Clause Type: {clause_type}

Clause Text:
{clause_text}

Provide your adversarial analysis of how this clause could be weaponized against the user:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error in adversary analysis: {type(e).__name__}")
            return "Unable to generate adversarial analysis due to technical error. Manual legal review recommended."
