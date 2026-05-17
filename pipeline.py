import os
from google.cloud import firestore
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from parser.pdf_parser import parse_pdf
from parser.docx_parser import parse_docx
from segmenter.clause_segmenter import segment_text

# TODO: Set GCP Project ID in environment or initialize implicitly
# e.g., db = firestore.Client(project=os.getenv("GCP_PROJECT_ID", "your-project-id"))
db = firestore.Client()

# TODO: Set Backend URL in environment
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def update_job_status(job_id: str, status: str, clause_count: int = 0, error: str = None):
    """
    Updates the job status document in Firestore.
    """
    doc_ref = db.collection("jobs").document(job_id)
    data = {
        "status": status,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    if clause_count > 0:
        data["clause_count"] = clause_count
    if error:
        data["error"] = error
        
    # Use set with merge=True to create if it doesn't exist, or update if it does.
    doc_ref.set(data, merge=True)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=8))
async def post_to_backend(payload: dict):
    """
    Posts the processed clauses to the backend ingestion API with exponential backoff.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/pipeline/ingest", 
            json=payload, 
            timeout=30.0
        )
        response.raise_for_status()

async def process_document(job_id: str, file_path: str, original_filename: str):
    """
    Main orchestration function for the document ingestion pipeline.
    """
    try:
        # Initial status
        update_job_status(job_id, "processing")
        
        # 1. Parse Document
        if original_filename.lower().endswith('.pdf'):
            blocks = parse_pdf(file_path)
        elif original_filename.lower().endswith('.docx'):
            blocks = parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format for {original_filename}")
            
        # 2. Segment Text
        clauses = segment_text(blocks)
        
        # Update status mid-way
        update_job_status(job_id, "segmentation_complete", clause_count=len(clauses))
        
        # 3. Store Clauses in Firestore (Batch Write)
        batch = db.batch()
        for clause in clauses:
            doc_ref = db.collection("clauses").document(job_id).collection("items").document(clause["id"])
            
            clause_data = {
                "id": clause["id"],
                "text": clause["text"],
                "type": clause["type"],
                "page_num": clause["page"], # Using page_num for firestore consistency, or 'page' based on contract
                "paragraph_index": clause["paragraph_index"],
                "job_id": job_id,
                "created_at": firestore.SERVER_TIMESTAMP
            }
            batch.set(doc_ref, clause_data)
        
        batch.commit()
        
        # 4. Trigger Backend Webhook
        # The contract expects: {"job_id": "string", "clauses": [{"id": "string", "text": "string", "type": "string", "page": int}]}
        backend_payload = {
            "job_id": job_id,
            "clauses": clauses
        }
        
        await post_to_backend(backend_payload)
        
        # Final success status
        update_job_status(job_id, "complete", clause_count=len(clauses))
        
    except Exception as e:
        print(f"Pipeline error for job {job_id}: {e}")
        update_job_status(job_id, "failed", error=str(e))
