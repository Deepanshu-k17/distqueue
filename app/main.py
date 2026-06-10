from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="DistQueue")

jobs = {}


class JobCreate(BaseModel):
    task_type: str
    payload: dict = Field(default_factory=dict)
    priority: int = 5


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


@app.post("/jobs")
def create_job(request: JobCreate):
    job_id = f"job_{uuid4().hex}"

    job = {
        "job_id": job_id,
        "task_type": request.task_type,
        "payload": request.payload,
        "priority": request.priority,
        "status": "pending"
    }

    jobs[job_id] = job

    return job


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]