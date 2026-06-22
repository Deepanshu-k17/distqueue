import argparse
import time

from app.database import SessionLocal
from app.queue_ops import pop_ready_job
from app.services import execute_job


def run_worker(queue_name: str, poll_interval: float):
    print(f"Worker started for queue='{queue_name}'")

    while True:
        job_id = pop_ready_job(queue_name)

        if job_id is None:
            print("No job found. Sleeping...")
            time.sleep(poll_interval)
            continue

        print(f"Picked job: {job_id}")

        db = SessionLocal()

        try:
            result = execute_job(db, job_id)
            print(f"Result: {result}")

        finally:
            db.close()


def main():
    parser = argparse.ArgumentParser(description="DistQueue worker")
    parser.add_argument("--queue", default="default")
    parser.add_argument("--poll-interval", type=float, default=2.0)

    args = parser.parse_args()

    run_worker(args.queue, args.poll_interval)


if __name__ == "__main__":
    main()