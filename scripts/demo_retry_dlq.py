import time
import requests

API_BASE_URL = "http://127.0.0.1:8000"


def create_failing_job():
    response = requests.post(
        f"{API_BASE_URL}/jobs",
        json={
            "queue": "default",
            "task_type": "fail_task",
            "payload": {},
            "priority": 5,
            "delay_seconds": 0,
            "max_retries": 2
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_job(job_id: str):
    response = requests.get(f"{API_BASE_URL}/jobs/{job_id}", timeout=10)
    response.raise_for_status()
    return response.json()


def get_dead_jobs():
    response = requests.get(
        f"{API_BASE_URL}/jobs/dead",
        params={"queue": "default"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def main():
    print("Creating fail_task job...")
    job = create_failing_job()
    job_id = job["job_id"]

    print(f"Created job: {job_id}")
    print(f"Initial status: {job['status']}")

    while True:
        current = get_job(job_id)

        print(
            f"status={current['status']}, "
            f"attempts={current['attempts']}, "
            f"max_retries={current['max_retries']}, "
            f"error={current['error_message']}"
        )

        if current["status"] == "dead":
            break

        time.sleep(3)

    dead_jobs = get_dead_jobs()
    found = any(dead_job["job_id"] == job_id for dead_job in dead_jobs)

    print(f"Dead job visible in GET /jobs/dead: {found}")


if __name__ == "__main__":
    main()
