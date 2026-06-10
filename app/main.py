from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="DistQueue")

jobs = {}


class JobStatus(str, Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class JobCreate(BaseModel):
    task_type: str
    payload: dict = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)


class JobStatusUpdate(BaseModel):
    status: JobStatus


class JobResponse(BaseModel):
    job_id: str
    task_type: str
    payload: dict
    priority: int
    status: JobStatus


@app.get("/")
def root():
    return {
        "message": "DistQueue API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(request: JobCreate):
    job_id = f"job_{uuid4().hex}"

    job = {
        "job_id": job_id,
        "task_type": request.task_type,
        "payload": request.payload,
        "priority": request.priority,
        "status": JobStatus.pending
    }

    jobs[job_id] = job

    return job


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs(status_filter: JobStatus | None = None):
    if status_filter is None:
        return list(jobs.values())

    return [
        job for job in jobs.values()
        if job["status"] == status_filter
    ]


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return jobs[job_id]


@app.patch("/jobs/{job_id}/status", response_model=JobResponse)
def update_job_status(job_id: str, request: JobStatusUpdate):
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    jobs[job_id]["status"] = request.status
    return jobs[job_id]


@app.post("/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    current_status = jobs[job_id]["status"]

    if current_status in [JobStatus.done, JobStatus.failed, JobStatus.cancelled]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status {current_status}"
        )

    jobs[job_id]["status"] = JobStatus.cancelled
    return jobs[job_id]