from uuid import uuid4

from app.models import JobStatus
from app.schemas import JobCreate


jobs = {}


def create_job(request: JobCreate):
    job_id = f"job_{uuid4().hex}"

    job = {
        "job_id": job_id,
        "task_type": request.task_type,
        "payload": request.payload,
        "priority": request.priority,
        "status": JobStatus.pending,
    }

    jobs[job_id] = job
    return job


def list_jobs(status_filter: JobStatus | None = None):
    if status_filter is None:
        return list(jobs.values())

    return [
        job for job in jobs.values()
        if job["status"] == status_filter
    ]


def get_job(job_id: str):
    return jobs.get(job_id)


def update_job_status(job_id: str, new_status: JobStatus):
    if job_id not in jobs:
        return None

    jobs[job_id]["status"] = new_status
    return jobs[job_id]


def cancel_job(job_id: str):
    if job_id not in jobs:
        return None

    current_status = jobs[job_id]["status"]

    if current_status in [JobStatus.done, JobStatus.failed, JobStatus.cancelled]:
        return "invalid_state"

    jobs[job_id]["status"] = JobStatus.cancelled
    return jobs[job_id]