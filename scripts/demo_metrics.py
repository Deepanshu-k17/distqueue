import requests

API_BASE_URL = "http://127.0.0.1:8000"


def main():
    response = requests.get(
        f"{API_BASE_URL}/metrics",
        params={"queue": "default"},
        timeout=10,
    )
    response.raise_for_status()
    metrics = response.json()

    print("DistQueue Metrics")
    print("-----------------")
    print(f"Queue: {metrics['queue']}")
    print(f"Ready queue depth: {metrics['redis']['ready_queue_depth']}")
    print(f"Delayed queue depth: {metrics['redis']['delayed_queue_depth']}")
    print(f"Dead queue depth: {metrics['redis']['dead_queue_depth']}")
    print(f"Total jobs: {metrics['database']['total_jobs']}")
    print(f"Status counts: {metrics['database']['status_counts']}")
    print(f"Completed jobs counted for latency: {metrics['latency']['completed_jobs_count']}")
    print(f"Average latency ms: {metrics['latency']['average_latency_ms']}")


if __name__ == "__main__":
    main()
