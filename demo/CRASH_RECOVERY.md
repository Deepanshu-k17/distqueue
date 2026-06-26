# Crash Recovery Demo

This demo proves that DistQueue can recover a job if a worker crashes while executing it.

## Start the System

```bash
docker compose up --build

For faster testing, set scheduler lock timeout to 10 seconds if running manually:

python scheduler.py --queue default --poll-interval 2 --lock-timeout 10
Step 1 — Submit a Long Task

Create this job through Swagger:

{
  "queue": "default",
  "task_type": "long_task",
  "payload": {
    "seconds": 60
  },
  "priority": 8,
  "delay_seconds": 0,
  "max_retries": 3
}
Step 2 — Confirm It Is Running

Call:

GET /jobs/{job_id}

Expected:

{
  "status": "running",
  "locked_by": "worker_...",
  "locked_at": "..."
}
Step 3 — Kill the Worker

Stop the worker process/container.

Manual worker:

Ctrl + C

Docker worker:

docker stop distqueue-worker

The job should remain stuck in running.

Step 4 — Wait for Scheduler Recovery

After the lock timeout, scheduler should recover it.

Expected scheduler log:

Recovered 1 stuck job(s)
Recovered stuck job: job_...

Call:

GET /jobs/{job_id}

Expected:

{
  "status": "queued",
  "locked_by": null,
  "locked_at": null
}
Step 5 — Restart Worker
docker start distqueue-worker

or manually:

python worker.py --queue default --worker-id worker_2 --concurrency 1 --poll-interval 1

Expected final state:

{
  "status": "done",
  "completed_at": "...",
  "locked_by": null,
  "locked_at": null
}
What This Proves
Worker ownership is tracked using locked_by and locked_at.
Crashed workers can leave jobs stuck in running.
Scheduler detects stale locks.
Scheduler requeues stuck jobs.
Another worker can complete the recovered job.
EOF

---

## Step 5 — Update README demo section

Add this section to your `README.md`:

```md
## Demo Scripts

DistQueue includes demo scripts for verifying core queue behavior.

Run the full system:

```bash
docker compose up --build

Then run demos from another terminal:

source .venv/bin/activate
python scripts/demo_immediate_job.py
python scripts/demo_delayed_job.py
python scripts/demo_retry_dlq.py
python scripts/demo_metrics.py

The demo scripts cover:

immediate job execution
delayed job scheduling
retry and dead-letter queue behavior
metrics endpoint output

Crash recovery is documented separately:

demo/CRASH_RECOVERY.md

---

## Step 6 — Final verification checklist

Run all:

```bash
python scripts/demo_immediate_job.py
python scripts/demo_delayed_job.py
python scripts/demo_retry_dlq.py
python scripts/demo_metrics.py

Then check:

docker ps
docker logs --tail 30 distqueue-worker
docker logs --tail 30 distqueue-scheduler