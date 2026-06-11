from fastapi import APIRouter, HTTPException, status

from app.models import JobStatus
from app.schemas import JobCreate, JobResponse, JobStatusUpdate
from app import services

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(request: JobCreate):
    return services.create_job(request)


@router.get("", response_model=list[JobResponse])
def list_jobs(status_filter: JobStatus | None = None):
    return services.list_jobs(status_filter)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    job = services.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


@router.patch("/{job_id}/status", response_model=JobResponse)
def update_job_status(job_id: str, request: JobStatusUpdate):
    job = services.update_job_status(job_id, request.status)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


@router.post("/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str):
    result = services.cancel_job(job_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if result == "invalid_state":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed, failed, or already cancelled job"
        )

    return result