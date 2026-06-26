import time

import requests


API_BASE_URL = "http://127.0.0.1:8000"


def create_delayed_job(delay_seconds: int):
    response = requests.post(
        f"{API_BASE_URL}/jobs",
        json={
            "queue": "default",
            "task_type": "sleep_task",
            "payload": {
                "seconds": 10
            },
            "priority": 8,
            "delay_seconds": delay_seconds,
            "max_retries": 3
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def get_job(job_id: str):
    response = requests.get(
        f"{API_BASE_URL}/jobs/{job_id}",
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def main():
    delay_seconds = 10

    print(f"Creating delayed job with delay_seconds={delay_seconds}...")
    job = create_delayed_job(delay_seconds)
    job_id = job["job_id"]

    print(f"Created job: {job_id}")
    print(f"Initial status: {job['status']}")
    print(f"run_at: {job['run_at']}")

    while True:
        current = get_job(job_id)
        status = current["status"]

        print(f"Current status: {status}")

        if status in ["done", "failed", "dead", "cancelled"]:
            print("Final job:")
            print(current)
            break

        time.sleep(2)


if __name__ == "__main__":
    main()
