from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db_models import JobDB
from app.models import JobStatus
from app.schemas import JobCreate


def db_job_to_response(job: JobDB):
    return {
        "job_id": job.id,
        "queue": job.queue_name,
        "task_type": job.task_type,
        "payload": job.payload,
        "priority": job.priority,
        "status": job.status,
        "attempts": job.attempts,
        "max_retries": job.max_retries,
        "run_at": job.run_at,
        "locked_by": job.locked_by,
        "locked_at": job.locked_at,
        "error_message": job.error_message,
        "completed_at": job.completed_at,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def create_job(db: Session, request: JobCreate):
    now = datetime.now(timezone.utc)
    run_at = now + timedelta(seconds=request.delay_seconds)

    job = JobDB(
        queue_name=request.queue,
        task_type=request.task_type,
        payload=request.payload,
        priority=request.priority,
        status=JobStatus.pending.value,
        attempts=0,
        max_retries=request.max_retries,
        run_at=run_at,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return db_job_to_response(job)


def list_jobs(db: Session, status_filter: JobStatus | None = None):
    query = db.query(JobDB)

    if status_filter is not None:
        query = query.filter(JobDB.status == status_filter.value)

    jobs = query.order_by(JobDB.created_at.desc()).all()

    return [db_job_to_response(job) for job in jobs]


def get_job(db: Session, job_id: str):
    job = db.query(JobDB).filter(JobDB.id == job_id).first()

    if job is None:
        return None

    return db_job_to_response(job)


def update_job_status(db: Session, job_id: str, new_status: JobStatus):
    job = db.query(JobDB).filter(JobDB.id == job_id).first()

    if job is None:
        return None

    job.status = new_status.value

    if new_status == JobStatus.done:
        job.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)

    return db_job_to_response(job)


def cancel_job(db: Session, job_id: str):
    job = db.query(JobDB).filter(JobDB.id == job_id).first()

    if job is None:
        return None

    if job.status in [
        JobStatus.done.value,
        JobStatus.failed.value,
        JobStatus.cancelled.value,
    ]:
        return "invalid_state"

    job.status = JobStatus.cancelled.value

    db.commit()
    db.refresh(job)

    return db_job_to_response(job)