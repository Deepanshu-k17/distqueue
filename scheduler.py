import argparse
import time

from app.database import SessionLocal
from app.services import move_due_delayed_jobs, recover_stuck_jobs


def run_scheduler(
    queue_name: str,
    poll_interval: float,
    lock_timeout_seconds: int,
):
    print(
        f"Scheduler started for queue='{queue_name}', "
        f"lock_timeout_seconds={lock_timeout_seconds}"
    )

    while True:
        db = SessionLocal()

        try:
            moved_jobs = move_due_delayed_jobs(db, queue_name)

            if moved_jobs:
                print(f"Moved {len(moved_jobs)} delayed job(s) to ready queue")
                for job in moved_jobs:
                    print(f"Moved delayed job: {job['job_id']}")

            recovered_jobs = recover_stuck_jobs(
                db=db,
                queue_name=queue_name,
                lock_timeout_seconds=lock_timeout_seconds,
            )

            if recovered_jobs:
                print(f"Recovered {len(recovered_jobs)} stuck job(s)")
                for job in recovered_jobs:
                    print(f"Recovered stuck job: {job['job_id']}")

            if not moved_jobs and not recovered_jobs:
                print("No due delayed or stuck jobs. Sleeping...")

        finally:
            db.close()

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="DistQueue scheduler")
    parser.add_argument("--queue", default="default")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--lock-timeout", type=int, default=30)

    args = parser.parse_args()

    run_scheduler(
        queue_name=args.queue,
        poll_interval=args.poll_interval,
        lock_timeout_seconds=args.lock_timeout,
    )


if __name__ == "__main__":
    main()