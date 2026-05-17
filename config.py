"""Configuration management for LexGuard RiskScope backend."""
import os
from google.cloud import secretmanager
from functools import lru_cache

# TODO: Replace YOUR_PROJECT_ID with actual GCP project ID
# TODO: Replace secret names with actual Secret Manager secret names
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "YOUR_PROJECT_ID")
GEMINI_API_KEY_SECRET = "lexguard-gemini-api-key"


@lru_cache(maxsize=10)
def get_secret(secret_name: str) -> str:
    """
    Retrieve secret from GCP Secret Manager.
    
    Args:
        secret_name: Name of the secret in Secret Manager
        
    Returns:
        Secret value as string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        # Never log the actual secret or detailed error that might expose secrets
        print(f"Error accessing secret {secret_name}: type={type(e).__name__}")
        raise


def get_gemini_api_key() -> str:
    """Get Gemini API key from Secret Manager."""
    return get_secret(GEMINI_API_KEY_SECRET)
