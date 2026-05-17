"""Extractor Agent - Classifies clauses by type."""
import google.generativeai as genai
from config import get_gemini_api_key


class ExtractorAgent:
    """Classifies contract clauses into predefined types."""
    
    CLAUSE_TYPES = [
        "non-compete",
        "IP-transfer",
        "arbitration",
        "termination",
        "data-collection",
        "liability",
        "auto-renewal",
        "other"
    ]
    
    def __init__(self):
        """Initialize the extractor agent with Gemini."""
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def classify_clause(self, clause_text: str) -> str:
        """
        Classify a clause into one of the predefined types.
        
        Args:
            clause_text: The text of the clause to classify
            
        Returns:
            Clause type as string (one of CLAUSE_TYPES)
        """
        prompt = f"""You are a legal contract analyzer. Classify the following contract clause into exactly ONE of these categories:

Categories:
- non-compete: Restrictions on working for competitors or starting competing businesses
- IP-transfer: Transfer of intellectual property rights, patents, copyrights, or inventions
- arbitration: Dispute resolution through arbitration instead of courts
- termination: Conditions for ending the contract or employment
- data-collection: Collection, use, or sharing of personal or business data
- liability: Limitation of liability, indemnification, or warranty disclaimers
- auto-renewal: Automatic contract renewal clauses
- other: Any clause that doesn't fit the above categories

Clause text:
{clause_text}

Respond with ONLY the category name, nothing else."""

        try:
            response = self.model.generate_content(prompt)
            classification = response.text.strip().lower()
            
            # Validate response is one of our types
            if classification in self.CLAUSE_TYPES:
                return classification
            else:
                # Default to 'other' if response is invalid
                return "other"
                
        except Exception as e:
            print(f"Error in clause classification: {type(e).__name__}")
            return "other"
