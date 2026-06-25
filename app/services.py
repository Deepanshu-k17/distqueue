from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db_models import JobDB
from app.models import JobStatus
from app.schemas import JobCreate
from app.queue_ops import enqueue_delayed_job, enqueue_ready_job
from app.tasks import execute_task

from app.queue_ops import (
    dead_queue_depth,
    delayed_queue_depth,
    enqueue_dead_job,
    enqueue_delayed_job,
    enqueue_ready_job,
    get_due_delayed_jobs,
    list_dead_jobs,
    ready_queue_depth,
    remove_delayed_job,
)

BASE_RETRY_DELAY_SECONDS = 5


def calculate_retry_delay(attempts: int):
    return BASE_RETRY_DELAY_SECONDS * (2 ** attempts)

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

    if request.delay_seconds == 0:
        enqueue_ready_job(job.queue_name, job.id, job.priority)
        job.status = JobStatus.queued.value
        db.commit()
        db.refresh(job)
    else:
        enqueue_delayed_job(job.queue_name, job.id, run_at.timestamp())
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

def get_job_db_object(db: Session, job_id: str):
    return db.query(JobDB).filter(JobDB.id == job_id).first()


def mark_job_running(db: Session, job: JobDB, worker_id: str):
    job.status = JobStatus.running.value
    job.locked_by = worker_id
    job.locked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)

    return job

def mark_job_done(db: Session, job: JobDB):
    job.status = JobStatus.done.value
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = None
    job.locked_by = None
    job.locked_at = None

    db.commit()
    db.refresh(job)

    return job


def mark_job_failed(db: Session, job: JobDB, error_message: str):
    job.attempts += 1
    job.error_message = error_message

    if job.attempts < job.max_retries:
        retry_delay = calculate_retry_delay(job.attempts)
        retry_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)

        job.status = JobStatus.pending.value
        job.run_at = retry_at
        job.locked_by = None
        job.locked_at = None

        db.commit()
        db.refresh(job)

        enqueue_delayed_job(
            queue_name=job.queue_name,
            job_id=job.id,
            run_at_timestamp=retry_at.timestamp(),
        )

        return {
            "status": "scheduled_retry",
            "job_id": job.id,
            "attempts": job.attempts,
            "max_retries": job.max_retries,
            "retry_delay_seconds": retry_delay,
            "run_at": retry_at,
            "error": error_message,
        }

    job.status = JobStatus.dead.value
    job.locked_by = None
    job.locked_at = None

    db.commit()
    db.refresh(job)

    enqueue_dead_job(
        queue_name=job.queue_name,
        job_id=job.id,
    )

    return {
        "status": "dead",
        "job_id": job.id,
        "attempts": job.attempts,
        "max_retries": job.max_retries,
        "error": error_message,
    }

def execute_job(db: Session, job_id: str, worker_id: str):
    job = get_job_db_object(db, job_id)

    if job is None:
        return {
            "status": "missing",
            "job_id": job_id,
        }

    if job.status in [
        JobStatus.done.value,
        JobStatus.cancelled.value,
        JobStatus.dead.value,
    ]:
        return {
            "status": "skipped",
            "job_id": job_id,
            "reason": f"Job already {job.status}",
        }

    mark_job_running(db, job, worker_id)

    try:
        execute_task(job.task_type, job.payload)
        mark_job_done(db, job)

        return {
            "status": "done",
            "job_id": job_id,
        }

    except Exception as exc:
        return mark_job_failed(db, job, str(exc))

def move_due_delayed_jobs(db: Session, queue_name: str, limit: int = 100):
    now_timestamp = datetime.now(timezone.utc).timestamp()

    due_job_ids = get_due_delayed_jobs(
        queue_name=queue_name,
        now_timestamp=now_timestamp,
        limit=limit,
    )

    moved_jobs = []

    for job_id in due_job_ids:
        job = db.query(JobDB).filter(JobDB.id == job_id).first()

        if job is None:
            remove_delayed_job(queue_name, job_id)
            continue

        if job.status != JobStatus.pending.value:
            remove_delayed_job(queue_name, job_id)
            continue

        remove_delayed_job(queue_name, job_id)
        enqueue_ready_job(job.queue_name, job.id, job.priority)

        job.status = JobStatus.queued.value

        db.commit()
        db.refresh(job)

        moved_jobs.append(db_job_to_response(job))

    return moved_jobs

def get_dead_jobs(db: Session, queue_name: str = "default"):
    dead_job_ids = list_dead_jobs(queue_name)

    dead_jobs = []

    for job_id in dead_job_ids:
        job = db.query(JobDB).filter(JobDB.id == job_id).first()

        if job is not None:
            dead_jobs.append(db_job_to_response(job))

    return dead_jobs

def retry_dead_job(db: Session, job_id: str):
    job = db.query(JobDB).filter(JobDB.id == job_id).first()

    if job is None:
        return None

    if job.status != JobStatus.dead.value:
        return "invalid_state"

    job.status = JobStatus.queued.value
    job.error_message = None
    job.run_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)

    enqueue_ready_job(job.queue_name, job.id, job.priority)

    return db_job_to_response(job)

def recover_stuck_jobs(
    db: Session,
    queue_name: str,
    lock_timeout_seconds: int = 30,
    limit: int = 100,
):
    cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=lock_timeout_seconds)

    stuck_jobs = (
        db.query(JobDB)
        .filter(JobDB.queue_name == queue_name)
        .filter(JobDB.status == JobStatus.running.value)
        .filter(JobDB.locked_at.isnot(None))
        .filter(JobDB.locked_at < cutoff_time)
        .limit(limit)
        .all()
    )

    recovered_jobs = []

    for job in stuck_jobs:
        job.status = JobStatus.queued.value
        job.locked_by = None
        job.locked_at = None

        db.commit()
        db.refresh(job)

        enqueue_ready_job(job.queue_name, job.id, job.priority)

        recovered_jobs.append(db_job_to_response(job))

    return recovered_jobs

def get_queue_metrics(db: Session, queue_name: str = "default"):
    total_jobs = db.query(JobDB).filter(JobDB.queue_name == queue_name).count()

    status_counts_raw = (
        db.query(JobDB.status, func.count(JobDB.id))
        .filter(JobDB.queue_name == queue_name)
        .group_by(JobDB.status)
        .all()
    )

    status_counts = {
        status: count
        for status, count in status_counts_raw
    }

    completed_jobs = (
        db.query(JobDB)
        .filter(JobDB.queue_name == queue_name)
        .filter(JobDB.status == JobStatus.done.value)
        .filter(JobDB.completed_at.isnot(None))
        .all()
    )

    latencies_ms = []

    for job in completed_jobs:
        if job.created_at is not None and job.completed_at is not None:
            latency = job.completed_at - job.created_at
            latencies_ms.append(latency.total_seconds() * 1000)

    average_latency_ms = None

    if latencies_ms:
        average_latency_ms = sum(latencies_ms) / len(latencies_ms)

    return {
        "queue": queue_name,
        "redis": {
            "ready_queue_depth": ready_queue_depth(queue_name),
            "delayed_queue_depth": delayed_queue_depth(queue_name),
            "dead_queue_depth": dead_queue_depth(queue_name),
        },
        "database": {
            "total_jobs": total_jobs,
            "status_counts": {
                "pending": status_counts.get(JobStatus.pending.value, 0),
                "queued": status_counts.get(JobStatus.queued.value, 0),
                "running": status_counts.get(JobStatus.running.value, 0),
                "done": status_counts.get(JobStatus.done.value, 0),
                "failed": status_counts.get(JobStatus.failed.value, 0),
                "dead": status_counts.get(JobStatus.dead.value, 0),
                "cancelled": status_counts.get(JobStatus.cancelled.value, 0),
            },
        },
        "latency": {
            "completed_jobs_count": len(latencies_ms),
            "average_latency_ms": average_latency_ms,
        },
    }