import time

from app.redis_client import redis_client


def ready_queue_key(queue_name: str) -> str:
    return f"queue:{queue_name}:ready"


def delayed_queue_key(queue_name: str) -> str:
    return f"queue:{queue_name}:delayed"


def enqueue_ready_job(queue_name: str, job_id: str, priority: int):
    score = (-priority * 1_000_000_000) + int(time.time() * 1000)

    redis_client.zadd(
        ready_queue_key(queue_name),
        {job_id: score},
    )


def enqueue_delayed_job(queue_name: str, job_id: str, run_at_timestamp: float):
    redis_client.zadd(
        delayed_queue_key(queue_name),
        {job_id: run_at_timestamp},
    )