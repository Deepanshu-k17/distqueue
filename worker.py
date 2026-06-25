import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from app.database import SessionLocal
from app.queue_ops import pop_ready_job
from app.services import execute_job


def process_one_job(queue_name: str, worker_id: str, poll_interval: float):
    while True:
        job_id = pop_ready_job(queue_name)

        if job_id is None:
            print(f"[{worker_id}] No job found. Sleeping...")
            time.sleep(poll_interval)
            continue

        print(f"[{worker_id}] Picked job: {job_id}")

        db = SessionLocal()

        try:
            result = execute_job(db, job_id, worker_id)
            print(f"[{worker_id}] Result: {result}")

        finally:
            db.close()


def run_worker(
    queue_name: str,
    poll_interval: float,
    worker_id: str,
    concurrency: int,
):
    print(
        f"Worker started: worker_id='{worker_id}', "
        f"queue='{queue_name}', concurrency={concurrency}"
    )

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for index in range(concurrency):
            thread_worker_id = f"{worker_id}_thread_{index + 1}"

            executor.submit(
                process_one_job,
                queue_name,
                thread_worker_id,
                poll_interval,
            )


def main():
    parser = argparse.ArgumentParser(description="DistQueue worker")
    parser.add_argument("--queue", default="default")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--worker-id", default=None)
    parser.add_argument("--concurrency", type=int, default=1)

    args = parser.parse_args()

    if args.concurrency < 1:
        raise ValueError("concurrency must be at least 1")

    worker_id = args.worker_id or f"worker_{uuid4().hex[:8]}"

    run_worker(
        queue_name=args.queue,
        poll_interval=args.poll_interval,
        worker_id=worker_id,
        concurrency=args.concurrency,
    )


if __name__ == "__main__":
    main()