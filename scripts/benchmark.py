import argparse
import statistics
import time
from datetime import datetime

import requests


API_BASE_URL = "http://127.0.0.1:8000"


def parse_datetime(value: str):
    if value is None:
        return None

    # FastAPI usually returns ISO timestamp.
    # Replace Z if present for compatibility.
    value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def create_job(seconds: int, priority: int):
    response = requests.post(
        f"{API_BASE_URL}/jobs",
        json={
            "queue": "default",
            "task_type": "sleep_task",
            "payload": {
                "seconds": seconds
            },
            "priority": priority,
            "delay_seconds": 0,
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


def percentile(values, percentile_value):
    if not values:
        return None

    sorted_values = sorted(values)
    index = int((percentile_value / 100) * len(sorted_values)) - 1
    index = max(0, min(index, len(sorted_values) - 1))

    return sorted_values[index]


def run_benchmark(job_count: int, task_seconds: int, priority: int, poll_interval: float):
    print(f"Submitting {job_count} jobs...")

    benchmark_start = time.time()
    submitted_jobs = []

    for index in range(job_count):
        job = create_job(seconds=task_seconds, priority=priority)
        submitted_jobs.append(job)

        print(f"Submitted {index + 1}/{job_count}: {job['job_id']}")

    submit_end = time.time()

    job_ids = [job["job_id"] for job in submitted_jobs]
    completed = {}
    failed_or_dead = {}

    print("Waiting for jobs to finish...")

    while len(completed) + len(failed_or_dead) < job_count:
        for job_id in job_ids:
            if job_id in completed or job_id in failed_or_dead:
                continue

            job = get_job(job_id)
            status = job["status"]

            if status == "done":
                completed[job_id] = job

            elif status in ["failed", "dead", "cancelled"]:
                failed_or_dead[job_id] = job

        print(
            f"Progress: done={len(completed)}, "
            f"failed/dead/cancelled={len(failed_or_dead)}, total={job_count}"
        )

        if len(completed) + len(failed_or_dead) < job_count:
            time.sleep(poll_interval)

    benchmark_end = time.time()

    latencies_ms = []

    for job in completed.values():
        created_at = parse_datetime(job["created_at"])
        completed_at = parse_datetime(job["completed_at"])

        if created_at is not None and completed_at is not None:
            latency_ms = (completed_at - created_at).total_seconds() * 1000
            latencies_ms.append(latency_ms)

    total_time = benchmark_end - benchmark_start
    submit_time = submit_end - benchmark_start
    completed_count = len(completed)
    failed_count = len(failed_or_dead)

    throughput = completed_count / total_time if total_time > 0 else 0

    print("\nBenchmark Results")
    print("-----------------")
    print(f"Submitted jobs: {job_count}")
    print(f"Completed jobs: {completed_count}")
    print(f"Failed/dead/cancelled jobs: {failed_count}")
    print(f"Submit time: {submit_time:.2f} sec")
    print(f"Total benchmark time: {total_time:.2f} sec")
    print(f"Throughput: {throughput:.2f} jobs/sec")

    if latencies_ms:
        print(f"Average latency: {statistics.mean(latencies_ms):.2f} ms")
        print(f"p50 latency: {percentile(latencies_ms, 50):.2f} ms")
        print(f"p95 latency: {percentile(latencies_ms, 95):.2f} ms")
        print(f"p99 latency: {percentile(latencies_ms, 99):.2f} ms")
        print(f"Min latency: {min(latencies_ms):.2f} ms")
        print(f"Max latency: {max(latencies_ms):.2f} ms")
    else:
        print("No completed jobs, latency could not be calculated.")


def main():
    parser = argparse.ArgumentParser(description="DistQueue benchmark script")
    parser.add_argument("--jobs", type=int, default=20)
    parser.add_argument("--seconds", type=int, default=1)
    parser.add_argument("--priority", type=int, default=5)
    parser.add_argument("--poll-interval", type=float, default=1.0)

    args = parser.parse_args()

    run_benchmark(
        job_count=args.jobs,
        task_seconds=args.seconds,
        priority=args.priority,
        poll_interval=args.poll_interval,
    )


if __name__ == "__main__":
    main()