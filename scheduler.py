import argparse
import time

from app.database import SessionLocal
from app.services import move_due_delayed_jobs


def run_scheduler(queue_name: str, poll_interval: float):
    print(f"Scheduler started for queue='{queue_name}'")

    while True:
        db = SessionLocal()

        try:
            moved_jobs = move_due_delayed_jobs(db, queue_name)

            if moved_jobs:
                print(f"Moved {len(moved_jobs)} delayed job(s) to ready queue")
                for job in moved_jobs:
                    print(f"Moved job: {job['job_id']}")
            else:
                print("No due delayed jobs. Sleeping...")

        finally:
            db.close()

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="DistQueue scheduler")
    parser.add_argument("--queue", default="default")
    parser.add_argument("--poll-interval", type=float, default=2.0)

    args = parser.parse_args()

    run_scheduler(args.queue, args.poll_interval)


if __name__ == "__main__":
    main()