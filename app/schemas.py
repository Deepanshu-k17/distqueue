from pydantic import BaseModel, Field

from app.models import JobStatus


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