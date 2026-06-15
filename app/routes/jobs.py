from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.models import JobStatus
from app.schemas import JobCreate, JobResponse, JobStatusUpdate

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(request: JobCreate, db: Session = Depends(get_db)):
    return services.create_job(db, request)


@router.get("", response_model=list[JobResponse])
def list_jobs(
    status_filter: JobStatus | None = None,
    db: Session = Depends(get_db),
):
    return services.list_jobs(db, status_filter)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = services.get_job(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return job


@router.patch("/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: str,
    request: JobStatusUpdate,
    db: Session = Depends(get_db),
):
    job = services.update_job_status(db, job_id, request.status)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return job


@router.post("/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    result = services.cancel_job(db, job_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if result == "invalid_state":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed, failed, or already cancelled job",
        )

    return result