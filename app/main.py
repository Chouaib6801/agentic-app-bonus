"""
FastAPI main application for the agentic research assistant.
Provides endpoints for job submission, status checking, and file downloads.
"""

import os
import uuid
from pathlib import Path
from typing import Optional

# Load .env file automatically (override=True to prioritize .env over system env vars)
from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rq import Queue
from rq.job import Job

from app.queue import get_redis_connection

# Configuration
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
USE_FAKE_REDIS = os.getenv("USE_FAKE_REDIS", "false").lower() == "true"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "jobs").mkdir(parents=True, exist_ok=True)

# Initialize FastAPI
app = FastAPI(
    title="Agentic Research Assistant",
    description="LLM-powered research assistant with Wikipedia integration",
    version="1.0.0"
)

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Redis connection (supports fakeredis for local dev)
redis_conn = get_redis_connection()
task_queue = Queue("tasks", connection=redis_conn, is_async=not USE_FAKE_REDIS)


# Pydantic models for API responses
class JobSubmitResponse(BaseModel):
    job_id: str
    status_url: str
    result_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    error: Optional[str] = None
    files: Optional[list] = None
    download_urls: Optional[dict] = None


@app.get("/")
async def serve_index():
    """Serve the main HTML UI."""
    return FileResponse(static_path / "index.html")


@app.post("/jobs", response_model=JobSubmitResponse)
async def create_job(
    prompt: str = Form(...),
    image: Optional[UploadFile] = File(None),
    context_text: Optional[str] = Form(None)
):
    """
    Create a new research job.
    
    - prompt: The research question or topic
    - image: Optional image file for multimodal input
    - context_text: Optional large text context to include
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create job directory
    job_dir = DATA_DIR / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle image upload if provided
    image_data = None
    if image and image.filename:
        content = await image.read()
        # Convert to base64 data URL for OpenAI
        import base64
        content_type = image.content_type or "image/png"
        image_b64 = base64.b64encode(content).decode("utf-8")
        image_data = f"data:{content_type};base64,{image_b64}"
        print(f"[Job {job_id}] Image uploaded: {image.filename} ({len(content)} bytes)")
    
    # Prepare job parameters
    job_params = {
        "job_id": job_id,
        "prompt": prompt,
        "image_data": image_data,
        "context_text": context_text,
        "job_dir": str(job_dir)
    }
    
    # Enqueue the job
    from app.tasks import run_research_job
    
    if USE_FAKE_REDIS:
        # Synchronous execution for local development (no worker needed)
        print(f"[Job {job_id}] Running synchronously (USE_FAKE_REDIS=true)...")
        try:
            run_research_job(job_params)
            # Store status in a simple file
            status_file = job_dir / ".status"
            status_file.write_text("finished")
        except Exception as e:
            status_file = job_dir / ".status"
            status_file.write_text(f"failed:{str(e)}")
            raise
    else:
        rq_job = task_queue.enqueue(
            run_research_job,
            job_params,
            job_id=job_id,
            job_timeout=600  # 10 minutes timeout
        )
        print(f"[Job {job_id}] Enqueued with prompt: {prompt[:100]}...")
    
    return JobSubmitResponse(
        job_id=job_id,
        status_url=f"/jobs/{job_id}",
        result_url=f"/jobs/{job_id}/files"
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a job."""
    job_dir = DATA_DIR / "jobs" / job_id
    
    if USE_FAKE_REDIS:
        # File-based status for local development
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail="Job not found")
        
        status_file = job_dir / ".status"
        if status_file.exists():
            status_content = status_file.read_text()
            if status_content.startswith("failed:"):
                status = "failed"
                error = status_content[7:]
            else:
                status = status_content
                error = None
        else:
            status = "started"
            error = None
    else:
        try:
            rq_job = Job.fetch(job_id, connection=redis_conn)
        except Exception:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Map RQ status to our status
        status_map = {
            "queued": "queued",
            "started": "started",
            "finished": "finished",
            "failed": "failed",
            "deferred": "queued",
            "scheduled": "queued"
        }
        status = status_map.get(rq_job.get_status(), "unknown")
        error = str(rq_job.exc_info) if status == "failed" and rq_job.exc_info else None
    
    response = JobStatusResponse(
        job_id=job_id,
        status=status,
        error=error
    )
    
    if status == "finished":
        # List output files
        if job_dir.exists():
            files = [f.name for f in job_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
            response.files = files
            response.download_urls = {
                f: f"/jobs/{job_id}/download/{f}" for f in files
            }
    
    return response


@app.get("/jobs/{job_id}/files")
async def list_job_files(job_id: str):
    """List all output files for a completed job."""
    job_dir = DATA_DIR / "jobs" / job_id
    
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Exclude hidden files (like .status)
    files = [f.name for f in job_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
    
    return {
        "job_id": job_id,
        "files": files,
        "download_urls": {f: f"/jobs/{job_id}/download/{f}" for f in files}
    }


@app.get("/jobs/{job_id}/download/{filename}")
async def download_file(job_id: str, filename: str):
    """Download a specific output file."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = DATA_DIR / "jobs" / job_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    media_types = {
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".json": "application/json"
    }
    suffix = file_path.suffix.lower()
    media_type = media_types.get(suffix, "application/octet-stream")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

