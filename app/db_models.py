import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class JobDB(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: f"job_{uuid.uuid4().hex}")

    queue_name = Column(String, nullable=False, default="default")
    task_type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)

    priority = Column(Integer, nullable=False, default=5)
    status = Column(String, nullable=False, default="pending")

    attempts = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)

    run_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)

    error_message = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())