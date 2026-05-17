import os
import uuid
import asyncio
import tempfile
from fastapi import FastAPI, UploadFile, File
from pipeline import process_document

app = FastAPI(title="LexGuard RiskScope Ingestion API")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

async def background_task_wrapper(job_id: str, file_path: str, original_filename: str):
    """
    Wraps the pipeline execution to ensure the temporary file is deleted 
    from the ephemeral container filesystem once processing finishes.
    """
    try:
        await process_document(job_id, file_path, original_filename)
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete temp file {file_path}: {e}")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    
    # Save the uploaded file to a temporary location
    _, ext = os.path.splitext(file.filename)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        content = await file.read()
        temp_file.write(content)
    finally:
        temp_file.close()
    
    # Launch the pipeline asynchronously without blocking the request
    asyncio.create_task(background_task_wrapper(job_id, temp_file.name, file.filename))
    
    return {"job_id": job_id}
