"""LexGuard RiskScope Backend - FastAPI application."""
import asyncio
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from models import IngestRequest, AnalysisReport, WebSocketEvent
from storage import FirestoreStorage
from orchestrator import Orchestrator


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        self.active_connections[job_id] = websocket
    
    def disconnect(self, job_id: str):
        """Remove WebSocket connection."""
        if job_id in self.active_connections:
            del self.active_connections[job_id]
    
    async def send_event(self, job_id: str, event: WebSocketEvent):
        """Send event to connected client."""
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_json(event.model_dump())
            except Exception as e:
                print(f"Error sending WebSocket event: {type(e).__name__}")
                self.disconnect(job_id)


# Global instances
storage = FirestoreStorage()
orchestrator = Orchestrator()
ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    print("LexGuard RiskScope backend starting...")
    yield
    # Shutdown
    print("LexGuard RiskScope backend shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="LexGuard RiskScope API",
    description="Contract intelligence platform with 4-agent orchestration",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy"}


@app.post("/api/pipeline/ingest")
async def ingest_clauses(request: IngestRequest):
    """
    Receive job_id + clauses array from pipeline.
    Creates a new analysis job in Firestore.
    
    Args:
        request: IngestRequest with job_id and clauses
        
    Returns:
        Success message with job_id
    """
    try:
        # Check if job already exists
        if storage.job_exists(request.job_id):
            raise HTTPException(
                status_code=409,
                detail=f"Job {request.job_id} already exists"
            )
        
        # Validate clauses
        if not request.clauses:
            raise HTTPException(
                status_code=400,
                detail="Clauses array cannot be empty"
            )
        
        # Create job in Firestore
        storage.create_job(request.job_id, request.clauses)
        
        return {
            "status": "success",
            "job_id": request.job_id,
            "total_clauses": len(request.clauses),
            "message": "Job created successfully. Use /api/analyze/{job_id} to start analysis."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in ingest: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def run_analysis_job(job_id: str):
    """
    Background task to run analysis on all clauses in a job.
    
    Args:
        job_id: Job identifier
    """
    try:
        # Update status to processing
        storage.update_job_status(job_id, "processing")
        
        # Get job data
        job = storage.get_job(job_id)
        if not job:
            return
        
        # Get original clauses from job
        job_ref = storage.db.collection(storage.jobs_collection).document(job_id)
        job_doc = job_ref.get()
        clauses_data = job_doc.to_dict().get("clauses", [])
        
        from models import Clause
        clauses = [Clause(**clause_data) for clause_data in clauses_data]
        
        # Define callback for WebSocket events
        async def event_callback(event_type: str, clause_id: str, data: dict):
            """Send WebSocket event and store completed analyses."""
            event = WebSocketEvent(
                event=event_type,
                clause_id=clause_id,
                data=data
            )
            await ws_manager.send_event(job_id, event)
            
            # Store completed clause analysis
            if event_type == "clause_complete":
                from models import ClauseAnalysis
                analysis = ClauseAnalysis(**data["analysis"])
                storage.add_clause_analysis(job_id, analysis)
        
        # Run orchestrator
        await orchestrator.analyze_job(clauses, event_callback)
        
        # Update status to completed
        storage.update_job_status(job_id, "completed")
        
        # Send job complete event
        await ws_manager.send_event(
            job_id,
            WebSocketEvent(event="job_complete", data={"job_id": job_id})
        )
        
    except Exception as e:
        print(f"Error in analysis job: {type(e).__name__}")
        storage.update_job_status(job_id, "failed")
        await ws_manager.send_event(
            job_id,
            WebSocketEvent(event="error", data={"error": "Analysis failed"})
        )


@app.get("/api/analyze/{job_id}")
async def analyze_job(job_id: str, background_tasks: BackgroundTasks):
    """
    Trigger agent chain for a job.
    Returns immediately and runs analysis in background.
    
    Args:
        job_id: Job identifier
        background_tasks: FastAPI background tasks
        
    Returns:
        Status message
    """
    try:
        # Check if job exists
        if not storage.job_exists(job_id):
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        # Get current job status
        job = storage.get_job(job_id)
        if job.status == "processing":
            return {
                "status": "already_processing",
                "job_id": job_id,
                "message": "Analysis already in progress"
            }
        
        if job.status == "completed":
            return {
                "status": "already_completed",
                "job_id": job_id,
                "message": "Analysis already completed. Use /api/report/{job_id} to retrieve results."
            }
        
        # Start analysis in background
        background_tasks.add_task(run_analysis_job, job_id)
        
        return {
            "status": "started",
            "job_id": job_id,
            "message": "Analysis started. Connect to /ws/{job_id} for real-time updates."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting analysis: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time analysis updates.
    Streams {event, clause_id, data} as each clause is analyzed.
    
    Args:
        websocket: WebSocket connection
        job_id: Job identifier
    """
    await ws_manager.connect(job_id, websocket)
    
    try:
        # Keep connection alive and listen for client messages
        while True:
            # Wait for any message from client (ping/pong)
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id)
    except Exception as e:
        print(f"WebSocket error: {type(e).__name__}")
        ws_manager.disconnect(job_id)


@app.get("/api/report/{job_id}", response_model=AnalysisReport)
async def get_report(job_id: str):
    """
    Get full JSON report for a completed job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        AnalysisReport with all clause analyses
    """
    try:
        # Get job from storage
        job = storage.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving report: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
