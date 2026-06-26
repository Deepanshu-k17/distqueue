# Local Benchmark Results

## Environment

- Local WSL Ubuntu environment
- FastAPI server running locally
- PostgreSQL and Redis running through Docker Compose
- Worker running locally
- Task type: `sleep_task`
- Task duration: 1 second per job

---

## Benchmark 1 — 50 jobs, worker concurrency 4

Command:

```bash
python scripts/benchmark.py --jobs 50 --seconds 1

Result:

Submitted jobs: 50
Completed jobs: 50
Failed/dead/cancelled jobs: 0
Submit time: 1.01 sec
Total benchmark time: 14.34 sec
Throughput: 3.49 jobs/sec
Average latency: 7209.72 ms
p50 latency: 7412.89 ms
p95 latency: 12182.25 ms
p99 latency: 13119.80 ms
Min latency: 1745.86 ms
Max latency: 13141.54 ms
Benchmark 2 — 100 jobs, worker concurrency 4

Command:

python scripts/benchmark.py --jobs 100 --seconds 1

Result:

Submitted jobs: 100
Completed jobs: 100
Failed/dead/cancelled jobs: 0
Submit time: 2.02 sec
Total benchmark time: 26.87 sec
Throughput: 3.72 jobs/sec
Average latency: 12703.60 ms
p50 latency: 12710.91 ms
p95 latency: 23210.92 ms
p99 latency: 24144.64 ms
Min latency: 1278.03 ms
Max latency: 24164.08 ms
Benchmark 3 — 20 jobs, worker concurrency 1

Command:

python worker.py --queue default --worker-id worker_c1 --concurrency 1 --poll-interval 1
python scripts/benchmark.py --jobs 20 --seconds 1

Result:

Submitted jobs: 20
Completed jobs: 20
Failed/dead/cancelled jobs: 0
Submit time: 0.51 sec
Total benchmark time: 21.06 sec
Throughput: 0.95 jobs/sec
Average latency: 10893.17 ms
p50 latency: 10376.05 ms
p95 latency: 19458.07 ms
p99 latency: 19458.07 ms
Min latency: 1350.21 ms
Max latency: 20458.08 ms
Benchmark 4 — 20 jobs, worker concurrency 4

Command:

python worker.py --queue default --worker-id worker_c4 --concurrency 4 --poll-interval 1
python scripts/benchmark.py --jobs 20 --seconds 1

Result:

Submitted jobs: 20
Completed jobs: 20
Failed/dead/cancelled jobs: 0
Submit time: 0.44 sec
Total benchmark time: 5.94 sec
Throughput: 3.37 jobs/sec
Average latency: 3172.04 ms
p50 latency: 3156.04 ms
p95 latency: 5115.41 ms
p99 latency: 5115.41 ms
Min latency: 1220.38 ms
Max latency: 5124.00 ms