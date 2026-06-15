from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import JobStatus


class JobCreate(BaseModel):
    queue: str = "default"
    task_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    delay_seconds: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0, le=10)


class JobStatusUpdate(BaseModel):
    status: JobStatus


class JobResponse(BaseModel):
    job_id: str
    queue: str
    task_type: str
    payload: dict[str, Any]
    priority: int
    status: JobStatus
    attempts: int
    max_retries: int
    run_at: datetime
    locked_by: str | None = None
    locked_at: datetime | None = None
    error_message: str | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None