"""
Job processing endpoints
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import pandas as pd
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
import logging

from config import settings
from models import UploadResponse, JobStatus, JobsList, JobSummary
from cortex_processor import ProcessingStatus
from routers.config import get_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["jobs"])

processing_jobs: dict[str, ProcessingStatus] = {}


def update_job_status(job_id: str, status: ProcessingStatus):
    """Update job status from processor"""
    if job_id in processing_jobs:
        processing_jobs[job_id] = status


async def process_questions(job_id: str, csv_path: Path):
    """Background task to process questions"""
    processor = get_processor()
    if not processor:
        logger.error(f"No processor available for job {job_id}")
        processing_jobs[job_id].status = "failed"
        processing_jobs[job_id].error = "Processor not configured"
        return

    try:
        processing_jobs[job_id].status = "processing"

        results = processor.process_csv(
            csv_path=csv_path,
            job_id=job_id,
            status_callback=lambda status: update_job_status(job_id, status)
        )

        output_json = settings.output_dir / f"{job_id}_results.json"
        output_csv = settings.output_dir / f"{job_id}_results.csv"

        with open(output_json, "w") as f:
            json.dump(results, f, indent=2, default=str)

        results_df = pd.DataFrame(results)
        results_df.to_csv(output_csv, index=False)

        processing_jobs[job_id].status = "completed"
        processing_jobs[job_id].completed_at = datetime.now()
        processing_jobs[job_id].output_json = str(output_json)
        processing_jobs[job_id].output_csv = str(output_csv)

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Processing error for job {job_id}: {e}")
        processing_jobs[job_id].status = "failed"
        processing_jobs[job_id].error = str(e)


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload CSV file with questions

    CSV should have columns: Id, Question
    """
    processor = get_processor()
    if not processor:
        raise HTTPException(
            status_code=400,
            detail="Please configure Snowflake connection first"
        )

    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    job_id = str(uuid.uuid4())
    upload_path = settings.upload_dir / f"{job_id}_{file.filename}"

    try:
        contents = await file.read()
        with open(upload_path, "wb") as f:
            f.write(contents)

        df = pd.read_csv(upload_path)
        df.columns = df.columns.str.strip()
        column_map = {col.lower(): col for col in df.columns}

        if 'id' not in column_map or 'question' not in column_map:
            raise HTTPException(
                status_code=400,
                detail="CSV must have 'Id' and 'Question' columns"
            )

        df = df.rename(columns={
            column_map['id']: 'Id',
            column_map['question']: 'Question'
        })

        num_questions = len(df)

        processing_jobs[job_id] = ProcessingStatus(
            job_id=job_id,
            status="queued",
            total=num_questions,
            processed=0,
            successful=0,
            failed=0,
            started_at=datetime.now()
        )

        background_tasks.add_task(process_questions, job_id, upload_path)

        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            num_questions=num_questions,
            status="queued",
            message="Processing started"
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get processing status for a job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    status = processing_jobs[job_id]

    return JobStatus(
        job_id=status.job_id,
        status=status.status,
        total=status.total,
        processed=status.processed,
        successful=status.successful,
        failed=status.failed,
        error_392708=status.error_392708,
        progress_percent=round((status.processed / status.total * 100), 1) if status.total > 0 else 0,
        started_at=status.started_at,
        completed_at=status.completed_at,
        error=status.error
    )


@router.get("/results/{job_id}/json")
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


@router.get("/results/{job_id}/csv")
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


@router.get("/jobs", response_model=JobsList)
async def list_jobs():
    """List all processing jobs"""
    jobs = [
        JobSummary(
            job_id=job_id,
            status=status.status,
            total=status.total,
            processed=status.processed,
            successful=status.successful,
            failed=status.failed,
            started_at=status.started_at,
            completed_at=status.completed_at
        )
        for job_id, status in processing_jobs.items()
    ]

    return JobsList(jobs=jobs)


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its files"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    status = processing_jobs[job_id]

    try:
        if status.output_json and os.path.exists(status.output_json):
            os.remove(status.output_json)
        if status.output_csv and os.path.exists(status.output_csv):
            os.remove(status.output_csv)

        for f in settings.upload_dir.glob(f"{job_id}_*"):
            os.remove(f)
    except Exception as e:
        logger.error(f"Error deleting files: {e}")

    del processing_jobs[job_id]

    return {"status": "success", "message": "Job deleted"}
