from enum import Enum


class JobStatus(str, Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"
    dead = "dead"
    cancelled = "cancelled"