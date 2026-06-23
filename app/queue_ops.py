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


def pop_ready_job(queue_name: str):
    result = redis_client.zpopmin(ready_queue_key(queue_name), 1)

    if not result:
        return None

    job_id, score = result[0]
    return job_id


def get_due_delayed_jobs(queue_name: str, now_timestamp: float, limit: int = 100):
    return redis_client.zrangebyscore(
        delayed_queue_key(queue_name),
        min=0,
        max=now_timestamp,
        start=0,
        num=limit,
    )


def remove_delayed_job(queue_name: str, job_id: str):
    redis_client.zrem(delayed_queue_key(queue_name), job_id)