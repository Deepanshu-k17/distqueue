import argparse
import requests


def create_jobs(count: int, seconds: int):
    url = "http://127.0.0.1:8000/jobs"

    for i in range(count):
        payload = {
            "queue": "default",
            "task_type": "sleep_task",
            "payload": {
                "seconds": seconds
            },
            "priority": 5,
            "delay_seconds": 0,
            "max_retries": 3
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        print(f"Created job {i + 1}/{count}: {data['job_id']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--seconds", type=int, default=3)

    args = parser.parse_args()

    create_jobs(args.count, args.seconds)


if __name__ == "__main__":
    main()