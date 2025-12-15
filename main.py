"""
Cortex Analyst UI - FastAPI Application
Processes questions through Snowflake Cortex Analyst API
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from cortex_processor import CortexProcessor, ProcessingStatus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cortex Analyst UI",
    description="Upload CSV questions and process them through Snowflake Cortex Analyst Please Look at snowflake-snowpark-python for more details",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Store active processing jobs
processing_jobs = {}

# Initialize processor (will be configured via API)
processor: Optional[CortexProcessor] = None


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI"""
    with open("static/index.html", "r") as f:
        return f.read()


@app.post("/api/configure")
async def configure_connection(config: dict):
    """
    Configure Snowflake connection
    
    Body:
    {
        "account": "your_account",
        "user": "your_user",
        "password": "your_password",
        "warehouse": "your_warehouse",
        "database": "CORTEX_ANALYST_DEMO",
        "schema": "OMNICHEM",
        "semantic_model": "@CORTEX_ANALYST_DEMO.OMNICHEM.RAW_DATA/OMNICHEM_V2_1_ENHANCED.yaml"
    }
    """
    global processor
    
    try:
        processor = CortexProcessor(
            account=config.get("account"),
            user=config.get("user"),
            password=config.get("password"),
            warehouse=config.get("warehouse"),
            database=config.get("database", "CORTEX_ANALYST_DEMO"),
            schema=config.get("schema", "OMNICHEM"),
            semantic_model=config.get("semantic_model")
        )
        
        # Test connection
        if processor.test_connection():
            return {"status": "success", "message": "Connection configured successfully"}
        else:
            return {"status": "error", "message": "Failed to connect to Snowflake"}
            
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/upload")
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload CSV file with questions
    
    CSV should have columns: Id, Question
    """
    if not processor:
        raise HTTPException(
            status_code=400,
            detail="Please configure Snowflake connection first"
        )
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    
    try:
        contents = await file.read()
        with open(upload_path, "wb") as f:
            f.write(contents)
        
        # Validate CSV structure
        df = pd.read_csv(upload_path)
        
        # Check for required columns (case-insensitive)
        df.columns = df.columns.str.strip()
        column_map = {col.lower(): col for col in df.columns}
        
        if 'id' not in column_map or 'question' not in column_map:
            raise HTTPException(
                status_code=400,
                detail="CSV must have 'Id' and 'Question' columns"
            )
        
        # Standardize column names
        df = df.rename(columns={
            column_map['id']: 'Id',
            column_map['question']: 'Question'
        })
        
        num_questions = len(df)
        
        # Initialize job status
        processing_jobs[job_id] = ProcessingStatus(
            job_id=job_id,
            status="queued",
            total=num_questions,
            processed=0,
            successful=0,
            failed=0,
            started_at=datetime.now()
        )
        
        # Start processing in background
        background_tasks.add_task(
            process_questions,
            job_id,
            upload_path
        )
        
        return {
            "job_id": job_id,
            "filename": file.filename,
            "num_questions": num_questions,
            "status": "queued",
            "message": "Processing started"
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def process_questions(job_id: str, csv_path: Path):
    """Background task to process questions"""
    try:
        # Update status
        processing_jobs[job_id].status = "processing"
        
        # Process questions
        results = processor.process_csv(
            csv_path=csv_path,
            job_id=job_id,
            status_callback=lambda status: update_job_status(job_id, status)
        )
        
        # Save results
        output_json = OUTPUT_DIR / f"{job_id}_results.json"
        output_csv = OUTPUT_DIR / f"{job_id}_results.csv"
        
        # Save JSON
        with open(output_json, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save CSV
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_csv, index=False)
        
        # Update final status
        processing_jobs[job_id].status = "completed"
        processing_jobs[job_id].completed_at = datetime.now()
        processing_jobs[job_id].output_json = str(output_json)
        processing_jobs[job_id].output_csv = str(output_csv)
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Processing error for job {job_id}: {e}")
        processing_jobs[job_id].status = "failed"
        processing_jobs[job_id].error = str(e)


def update_job_status(job_id: str, status: ProcessingStatus):
    """Update job status from processor"""
    if job_id in processing_jobs:
        processing_jobs[job_id] = status


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get processing status for a job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = processing_jobs[job_id]
    
    return {
        "job_id": status.job_id,
        "status": status.status,
        "total": status.total,
        "processed": status.processed,
        "successful": status.successful,
        "failed": status.failed,
        "error_392708": status.error_392708,
        "progress_percent": round((status.processed / status.total * 100), 1) if status.total > 0 else 0,
        "started_at": status.started_at.isoformat() if status.started_at else None,
        "completed_at": status.completed_at.isoformat() if status.completed_at else None,
        "error": status.error
    }


@app.get("/api/results/{job_id}/json")
async def download_json(job_id: str):
    """Download results as JSON"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = processing_jobs[job_id]
    
    if status.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if not status.output_json or not os.path.exists(status.output_json):
        raise HTTPException(status_code=404, detail="JSON file not found")
    
    return FileResponse(
        status.output_json,
        media_type="application/json",
        filename=f"results_{job_id}.json"
    )


@app.get("/api/results/{job_id}/csv")
async def download_csv(job_id: str):
    """Download results as CSV"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = processing_jobs[job_id]
    
    if status.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if not status.output_csv or not os.path.exists(status.output_csv):
        raise HTTPException(status_code=404, detail="CSV file not found")
    
    return FileResponse(
        status.output_csv,
        media_type="text/csv",
        filename=f"results_{job_id}.csv"
    )


@app.get("/api/jobs")
async def list_jobs():
    """List all processing jobs"""
    jobs = []
    for job_id, status in processing_jobs.items():
        jobs.append({
            "job_id": job_id,
            "status": status.status,
            "total": status.total,
            "processed": status.processed,
            "successful": status.successful,
            "failed": status.failed,
            "started_at": status.started_at.isoformat() if status.started_at else None,
            "completed_at": status.completed_at.isoformat() if status.completed_at else None
        })
    
    return {"jobs": jobs}


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its files"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = processing_jobs[job_id]
    
    # Delete files
    try:
        if status.output_json and os.path.exists(status.output_json):
            os.remove(status.output_json)
        if status.output_csv and os.path.exists(status.output_csv):
            os.remove(status.output_csv)
        
        # Find and delete upload file
        for f in UPLOAD_DIR.glob(f"{job_id}_*"):
            os.remove(f)
    except Exception as e:
        logger.error(f"Error deleting files: {e}")
    
    # Remove from jobs
    del processing_jobs[job_id]
    
    return {"status": "success", "message": "Job deleted"}


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
