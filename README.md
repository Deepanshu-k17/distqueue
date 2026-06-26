# DistQueue

DistQueue is a Redis-backed distributed task queue engine built with FastAPI, PostgreSQL, Redis, SQLAlchemy, Docker Compose, and Python worker processes.

It supports job submission through an API, durable job metadata storage in PostgreSQL, Redis-based queue dispatch, delayed jobs, automatic retries, dead-letter queues, worker execution, configurable worker concurrency, metrics, benchmarking, and worker crash recovery using leases.

---

## Documentation

* [Architecture](docs/ARCHITECTURE.md)
* [Interview Notes](docs/INTERVIEW_NOTES.md)
* [Current Limitations](docs/LIMITATIONS.md)
* [Crash Recovery Demo](demo/CRASH_RECOVERY.md)
* [Local Benchmark Results](benchmark_results/local_benchmark.md)

---

## Features

* FastAPI-based job submission API
* PostgreSQL-backed persistent job metadata
* Redis sorted sets for ready, delayed, and dead-letter queues
* Priority-based job dispatch
* Delayed job scheduling
* Background worker process for job execution
* Scheduler process for delayed jobs and stuck-job recovery
* Retry system with exponential backoff
* Dead-letter queue for exhausted jobs
* Manual dead-job inspection and retry
* Worker leases using `locked_by` and `locked_at`
* Crash recovery for jobs stuck in `running`
* Configurable worker concurrency using `ThreadPoolExecutor`
* Queue metrics endpoint
* Benchmark script for throughput and latency measurement
* Docker Compose setup for API, worker, scheduler, PostgreSQL, and Redis
* Clean backend structure using routes, schemas, services, database models, and queue utilities

---

## Architecture

```text
Client
  ↓
FastAPI API
  ↓
PostgreSQL stores full job metadata
  ↓
Redis stores job IDs for queue ordering
  ↓
Worker processes execute jobs
  ↓
Scheduler handles delayed jobs, retries, and stuck-job recovery
```

PostgreSQL is the durable source of truth.

Redis is the fast dispatch layer.

Workers execute tasks.

The scheduler moves delayed jobs into the ready queue and recovers stuck running jobs.

---

## Tech Stack

* Python
* FastAPI
* Pydantic
* Uvicorn
* PostgreSQL
* SQLAlchemy
* Redis
* Docker Compose

---

## Project Structure

```text
distqueue/
  app/
    __init__.py
    main.py
    config.py
    database.py
    db_models.py
    models.py
    schemas.py
    services.py
    queue_ops.py
    redis_client.py
    tasks.py
    routes/
      __init__.py
      jobs.py
      metrics.py
  scripts/
    benchmark.py
    create_jobs.py
    demo_immediate_job.py
    demo_delayed_job.py
    demo_retry_dlq.py
    demo_metrics.py
  docs/
    ARCHITECTURE.md
    INTERVIEW_NOTES.md
    LIMITATIONS.md
  demo/
    CRASH_RECOVERY.md
  benchmark_results/
    local_benchmark.md
  worker.py
  scheduler.py
  Dockerfile
  docker-compose.yml
  requirements.txt
  README.md
  .gitignore
```

---

## API Endpoints

| Method  | Endpoint                      | Purpose                   |
| ------- | ----------------------------- | ------------------------- |
| `GET`   | `/`                           | Check if API is running   |
| `GET`   | `/health`                     | Health check endpoint     |
| `POST`  | `/jobs`                       | Create a new job          |
| `GET`   | `/jobs`                       | List all jobs             |
| `GET`   | `/jobs?status_filter=pending` | Filter jobs by status     |
| `GET`   | `/jobs/dead?queue=default`    | List dead-letter jobs     |
| `GET`   | `/jobs/{job_id}`              | Get a specific job        |
| `PATCH` | `/jobs/{job_id}/status`       | Update job status         |
| `POST`  | `/jobs/{job_id}/cancel`       | Cancel a job              |
| `POST`  | `/jobs/{job_id}/retry`        | Manually retry a dead job |
| `GET`   | `/metrics?queue=default`      | Get queue and job metrics |

---

## Job Creation Example

Request:

```json
{
  "queue": "default",
  "task_type": "sleep_task",
  "payload": {
    "seconds": 3
  },
  "priority": 8,
  "delay_seconds": 0,
  "max_retries": 3
}
```

Response:

```json
{
  "job_id": "job_...",
  "queue": "default",
  "task_type": "sleep_task",
  "payload": {
    "seconds": 3
  },
  "priority": 8,
  "status": "queued",
  "attempts": 0,
  "max_retries": 3,
  "run_at": "...",
  "locked_by": null,
  "locked_at": null,
  "error_message": null,
  "completed_at": null,
  "created_at": "...",
  "updated_at": "..."
}
```

---

## Job Lifecycle

Supported job statuses:

```text
pending
queued
running
done
failed
dead
cancelled
```

Common lifecycle flows:

```text
Immediate job:
pending → queued → running → done
```

```text
Delayed job:
pending → queued → running → done
```

```text
Retryable failure:
queued → running → pending → queued → running → done
```

```text
Exhausted failure:
queued → running → pending → queued → running → dead
```

```text
Worker crash recovery:
queued → running → queued → running → done
```

---

## Job Fields

| Field                  | Purpose                                   |
| ---------------------- | ----------------------------------------- |
| `job_id`               | Unique job identifier                     |
| `queue` / `queue_name` | Queue where the job belongs               |
| `task_type`            | Type of task to execute                   |
| `payload`              | Task input data                           |
| `priority`             | Job priority from 1 to 10                 |
| `status`               | Current lifecycle state                   |
| `attempts`             | Number of failed execution attempts       |
| `max_retries`          | Maximum retry attempts allowed            |
| `run_at`               | Time when the job becomes eligible to run |
| `locked_by`            | Worker that claimed the job               |
| `locked_at`            | Time when the worker claimed the job      |
| `error_message`        | Failure reason if the job fails           |
| `completed_at`         | Time when the job finishes successfully   |
| `created_at`           | Job creation timestamp                    |
| `updated_at`           | Last update timestamp                     |

---

## Redis Queues

DistQueue uses Redis sorted sets for queue ordering.

Current Redis keys:

```text
queue:default:ready
queue:default:delayed
queue:default:dead
```

### Ready Queue

Immediate jobs are added to:

```text
queue:{queue_name}:ready
```

Ready queue score:

```text
score = (-priority * 1_000_000_000) + current_timestamp_ms
```

Higher-priority jobs get lower scores, so they are picked earlier.

### Delayed Queue

Delayed jobs and retry jobs are added to:

```text
queue:{queue_name}:delayed
```

Delayed queue score:

```text
score = run_at_timestamp
```

The scheduler moves jobs into the ready queue when:

```text
run_at <= current_time
```

### Dead-Letter Queue

Jobs that exhaust their retry attempts are added to:

```text
queue:{queue_name}:dead
```

Redis stores only job IDs. PostgreSQL stores the full job metadata.

---

## Worker

The worker is a separate long-running process that picks jobs from Redis and executes them.

Run worker manually:

```bash
python worker.py --queue default --worker-id worker_1 --concurrency 4 --poll-interval 1
```

Worker flow:

```text
ZPOPMIN queue:default:ready
  ↓
Get job_id
  ↓
Load job from PostgreSQL
  ↓
Mark job running
  ↓
Set locked_by and locked_at
  ↓
Execute task
  ↓
Mark done, schedule retry, or move to dead-letter queue
```

Supported task types:

```text
sleep_task
echo_task
fail_task
unstable_task
long_task
```

---

## Scheduler

The scheduler is a separate long-running process that handles delayed jobs and stuck running jobs.

Run scheduler manually:

```bash
python scheduler.py --queue default --poll-interval 2 --lock-timeout 30
```

Scheduler responsibilities:

* Move due delayed jobs into the ready queue
* Move due retry jobs into the ready queue
* Detect stuck running jobs using `locked_at`
* Requeue jobs whose worker lease has expired

Scheduler flow:

```text
Check delayed queue
  ↓
Move due jobs to ready queue
  ↓
Check running jobs with old locked_at
  ↓
Recover stuck jobs
  ↓
Sleep and repeat
```

---

## Retry System

When a task fails, the worker increments `attempts`.

If the job still has retries left, it is scheduled for retry using exponential backoff.

Retry behavior:

```text
task fails
  ↓
attempts += 1
  ↓
if attempts < max_retries:
    status = pending
    run_at = now + retry_delay
    enqueue into delayed queue
else:
    status = dead
    enqueue into dead-letter queue
```

Retry delay:

```text
retry_delay = base_delay * 2^attempts
```

Example with base delay of 5 seconds:

```text
attempt 1 failure → retry after 10 seconds
attempt 2 failure → retry after 20 seconds
attempt 3 failure → retry after 40 seconds
```

---

## Dead-Letter Queue

The dead-letter queue stores jobs that failed after exhausting all retry attempts.

A job becomes `dead` when:

```text
attempts >= max_retries
```

Dead jobs can be inspected through:

```text
GET /jobs/dead?queue=default
```

Dead jobs can be manually retried through:

```text
POST /jobs/{job_id}/retry
```

---

## Worker Crash Recovery

DistQueue uses worker leases to prevent jobs from getting stuck forever in `running`.

When a worker picks a job:

```text
status = running
locked_by = worker_id
locked_at = current_time
```

If the worker crashes before finishing, the job stays `running`.

The scheduler checks for running jobs where:

```text
locked_at < current_time - lock_timeout
```

Then it recovers the job:

```text
status = queued
locked_by = null
locked_at = null
job_id reinserted into Redis ready queue
```

A new worker can then pick and complete the job.

---

## Metrics

DistQueue exposes a basic metrics endpoint:

```text
GET /metrics?queue=default
```

The metrics endpoint reports:

* Redis ready queue depth
* Redis delayed queue depth
* Redis dead-letter queue depth
* Total jobs in PostgreSQL
* Job counts by status
* Completed job count
* Average completion latency

Example response:

```json
{
  "queue": "default",
  "redis": {
    "ready_queue_depth": 0,
    "delayed_queue_depth": 0,
    "dead_queue_depth": 1
  },
  "database": {
    "total_jobs": 20,
    "status_counts": {
      "pending": 0,
      "queued": 0,
      "running": 0,
      "done": 18,
      "failed": 0,
      "dead": 2,
      "cancelled": 0
    }
  },
  "latency": {
    "completed_jobs_count": 18,
    "average_latency_ms": 4230.5
  }
}
```

---

## Benchmark Results

DistQueue includes a benchmark script for submitting jobs, waiting for completion, and calculating throughput and latency.

Run benchmark:

```bash
python scripts/benchmark.py --jobs 50 --seconds 1
```

The benchmark reports:

* submitted jobs
* completed jobs
* failed/dead/cancelled jobs
* total benchmark time
* throughput in jobs/sec
* average latency
* p50 latency
* p95 latency
* p99 latency
* min/max latency

Local benchmark with `sleep_task` jobs showed that worker concurrency improves throughput significantly.

For 20 one-second jobs:

| Worker Concurrency |    Throughput | Average Latency | p95 Latency |
| ------------------ | ------------: | --------------: | ----------: |
| 1                  | 0.95 jobs/sec |     10893.17 ms | 19458.07 ms |
| 4                  | 3.37 jobs/sec |      3172.04 ms |  5115.41 ms |

With worker concurrency 4, DistQueue processed 100 one-second jobs at approximately:

```text
Throughput: 3.72 jobs/sec
p95 latency: 23210.92 ms
p99 latency: 24144.64 ms
```

Benchmark results were collected locally on WSL with PostgreSQL and Redis running through Docker Compose.

Detailed results are available in:

```text
benchmark_results/local_benchmark.md
```

---

## Docker Compose Setup

DistQueue can be run using Docker Compose.

Start all services:

```bash
docker compose up --build
```

This starts:

* PostgreSQL
* Redis
* FastAPI API
* Worker
* Scheduler

API docs:

```text
http://127.0.0.1:8000/docs
```

Useful commands:

```bash
docker logs -f distqueue-api
docker logs -f distqueue-worker
docker logs -f distqueue-scheduler
```

Stop services:

```bash
docker compose down
```

Stop services and delete database volume:

```bash
docker compose down -v
```

Inside Docker Compose, API, worker, and scheduler connect to PostgreSQL and Redis using service names:

```text
postgres:5432
redis:6379
```

not `localhost`.

---

## Running Locally Without Dockerized API/Worker

Start PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

Activate virtual environment:

```bash
source .venv/bin/activate
```

Run FastAPI server:

```bash
python -m uvicorn app.main:app --reload
```

Run worker:

```bash
python worker.py --queue default --worker-id worker_1 --concurrency 4 --poll-interval 1
```

Run scheduler:

```bash
python scheduler.py --queue default --poll-interval 2 --lock-timeout 30
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

---

## Demo Scripts

DistQueue includes demo scripts for verifying core queue behavior.

Run the full system:

```bash
docker compose up --build
```

Then run demos from another terminal:

```bash
source .venv/bin/activate
python scripts/demo_immediate_job.py
python scripts/demo_delayed_job.py
python scripts/demo_retry_dlq.py
python scripts/demo_metrics.py
```

The demo scripts cover:

* immediate job execution
* delayed job scheduling
* retry and dead-letter queue behavior
* metrics endpoint output

Crash recovery is documented separately:

```text
demo/CRASH_RECOVERY.md
```

---

## Manual Redis Checks

Open Redis CLI:

```bash
docker exec -it distqueue-redis redis-cli
```

Check ready queue:

```bash
ZRANGE queue:default:ready 0 -1 WITHSCORES
```

Check delayed queue:

```bash
ZRANGE queue:default:delayed 0 -1 WITHSCORES
```

Check dead queue:

```bash
ZRANGE queue:default:dead 0 -1 WITHSCORES
```

Clear queues during development:

```bash
DEL queue:default:ready
DEL queue:default:delayed
DEL queue:default:dead
```

---

## Manual PostgreSQL Checks

Open PostgreSQL:

```bash
docker exec -it distqueue-postgres psql -U distqueue -d distqueue
```

Check latest jobs:

```sql
SELECT id, queue_name, task_type, priority, status, attempts, max_retries, run_at, locked_by, locked_at, error_message, completed_at
FROM jobs
ORDER BY created_at DESC
LIMIT 10;
```

Exit:

```sql
\q
```

---

## Example Tests

### Successful Job

```json
{
  "queue": "default",
  "task_type": "sleep_task",
  "payload": {
    "seconds": 3
  },
  "priority": 8,
  "delay_seconds": 0,
  "max_retries": 3
}
```

Expected final status:

```text
done
```

### Delayed Job

```json
{
  "queue": "default",
  "task_type": "sleep_task",
  "payload": {
    "seconds": 3
  },
  "priority": 8,
  "delay_seconds": 10,
  "max_retries": 3
}
```

Expected flow:

```text
pending → queued → running → done
```

### Permanently Failing Job

```json
{
  "queue": "default",
  "task_type": "fail_task",
  "payload": {},
  "priority": 5,
  "delay_seconds": 0,
  "max_retries": 2
}
```

Expected final status:

```text
dead
```

### Crash Recovery Test

```json
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
```

Test:

```text
1. Start worker.
2. Submit long_task.
3. Confirm job becomes running with locked_by and locked_at.
4. Kill worker.
5. Wait for scheduler lock timeout.
6. Confirm scheduler requeues job.
7. Start new worker.
8. Confirm job becomes done.
```

---

## Current Limitations

* No Alembic migrations yet
* No production-grade observability yet
* No dashboard yet
* No authentication or authorization
* No rate limiting
* No retry jitter
* No heartbeat system yet
* No strong idempotency guarantees for tasks
* Thread-based concurrency is better for I/O-bound tasks than CPU-heavy tasks
* Recovered jobs may execute more than once in some edge cases

---

## Planned Improvements

* Add Alembic migrations
* Add task idempotency keys
* Add retry jitter
* Add p50/p95/p99 metrics endpoint
* Add dashboard
* Add authentication
* Add rate limiting
* Add structured logging
* Add pytest test suite
* Add Kubernetes deployment examples
