# DistQueue

DistQueue is a Redis-backed distributed task queue engine built step by step using FastAPI, PostgreSQL, Redis, SQLAlchemy, and Python worker processes.

The final goal is to build a backend system where users can submit jobs through an API, store durable job metadata in PostgreSQL, dispatch jobs through Redis queues, execute them using workers, support delayed jobs, retries, dead-letter queues, crash recovery, metrics, benchmarking, and Docker-based local setup.

This project is being built incrementally to understand backend systems properly instead of directly copy-pasting a large system.

---

## Current Status

Implemented so far:

* FastAPI backend
* Clean route/schema/service/model structure
* PostgreSQL persistence
* Redis ready and delayed queues
* Basic worker process
* Dummy task execution
* Job lifecycle updates
* Error tracking
* Completion timestamp tracking

Current flow:

```text
Client
  ↓
FastAPI API
  ↓
PostgreSQL stores full job metadata
  ↓
Redis stores job_id for queue ordering
  ↓
worker.py pops job_id from Redis
  ↓
Worker loads job from PostgreSQL
  ↓
Worker executes task
  ↓
Worker updates job status in PostgreSQL
```

---

## Tech Stack

Current:

* Python
* FastAPI
* Pydantic
* Uvicorn
* PostgreSQL
* SQLAlchemy
* Redis
* Docker Compose

Planned:

* Scheduler process
* Retry system
* Dead-letter queue
* Worker leases and crash recovery
* Metrics endpoint
* Benchmarking script
* WebSocket monitoring dashboard

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
  worker.py
  docker-compose.yml
  requirements.txt
  README.md
  .gitignore
```

---

## API Endpoints

| Method  | Endpoint                      | Purpose                 |
| ------- | ----------------------------- | ----------------------- |
| `GET`   | `/`                           | Check if API is running |
| `GET`   | `/health`                     | Health check endpoint   |
| `POST`  | `/jobs`                       | Create a new job        |
| `GET`   | `/jobs`                       | List all jobs           |
| `GET`   | `/jobs?status_filter=pending` | Filter jobs by status   |
| `GET`   | `/jobs/{job_id}`              | Get a specific job      |
| `PATCH` | `/jobs/{job_id}/status`       | Update job status       |
| `POST`  | `/jobs/{job_id}/cancel`       | Cancel a job            |

---

## Example Job Creation Request

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

Example response:

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

## Job Status Values

Allowed job statuses:

```text
pending
queued
running
done
failed
cancelled
```

Status lifecycle currently supported:

```text
queued -> running -> done
queued -> running -> failed
pending -> cancelled
queued -> cancelled
running -> cancelled
```

---

## Job Fields

| Field                  | Purpose                             |
| ---------------------- | ----------------------------------- |
| `job_id`               | Unique job identifier               |
| `queue` / `queue_name` | Queue where the job belongs         |
| `task_type`            | Type of task to execute             |
| `payload`              | Task input data                     |
| `priority`             | Job priority from 1 to 10           |
| `status`               | Current lifecycle state             |
| `attempts`             | Number of execution attempts        |
| `max_retries`          | Maximum retries allowed             |
| `run_at`               | Time when job is eligible to run    |
| `locked_by`            | Worker that claimed the job         |
| `locked_at`            | Time when worker claimed the job    |
| `error_message`        | Failure reason if job fails         |
| `completed_at`         | Time when job finishes successfully |
| `created_at`           | Job creation timestamp              |
| `updated_at`           | Last update timestamp               |

---

## Redis Queues

Redis is used as the fast queue dispatch layer.

PostgreSQL stores full durable job metadata.

Redis stores only job IDs and scores.

Current Redis keys:

```text
queue:default:ready
queue:default:delayed
```

### Ready Queue

Immediate jobs go into:

```text
queue:{queue_name}:ready
```

Ready queue uses Redis sorted sets.

Score logic:

```text
score = (-priority * 1_000_000_000) + current_timestamp_ms
```

Higher priority jobs receive lower scores, so they are picked earlier by Redis.

### Delayed Queue

Delayed jobs go into:

```text
queue:{queue_name}:delayed
```

Delayed queue score:

```text
score = run_at_timestamp
```

Later, the scheduler will move jobs from delayed queue to ready queue when `run_at <= current_time`.

---

## Worker

The worker is a separate long-running process that picks jobs from Redis and executes them.

Run worker:

```bash
python worker.py --queue default --poll-interval 2
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
Execute task
  ↓
If success: mark done and set completed_at
  ↓
If failure: mark failed and store error_message
```

Currently supported dummy tasks:

```text
sleep_task
echo_task
fail_task
```

Example successful task:

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

Example failing task:

```json
{
  "queue": "default",
  "task_type": "fail_task",
  "payload": {},
  "priority": 5,
  "delay_seconds": 0,
  "max_retries": 3
}
```

---

## Running Locally

### 1. Start PostgreSQL and Redis

```bash
docker compose up -d
```

Check containers:

```bash
docker ps
```

Expected:

```text
distqueue-postgres
distqueue-redis
```

### 2. Activate virtual environment

```bash
source .venv/bin/activate
```

### 3. Run FastAPI server

```bash
python -m uvicorn app.main:app --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

### 4. Run worker

Open another terminal:

```bash
cd /mnt/d/projects/distqueue
source .venv/bin/activate
python worker.py --queue default --poll-interval 2
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

Clear ready queue during development:

```bash
DEL queue:default:ready
```

Clear delayed queue during development:

```bash
DEL queue:default:delayed
```

---

## Manual PostgreSQL Checks

Open PostgreSQL:

```bash
docker exec -it distqueue-postgres psql -U distqueue -d distqueue
```

Check latest jobs:

```sql
SELECT id, queue_name, task_type, priority, status, attempts, max_retries, run_at, error_message, completed_at
FROM jobs
ORDER BY created_at DESC
LIMIT 5;
```

Exit:

```sql
\q
```

---

## Day-by-Day Progress

### Day 1 — Basic FastAPI Backend

Implemented:

* `GET /`
* `GET /health`
* `POST /jobs`
* `GET /jobs/{job_id}`
* In-memory job storage using a Python dictionary

Learned:

* Backend receives HTTP requests and returns HTTP responses.
* `GET` fetches data.
* `POST` sends data to create something.
* JSON is used to send structured data.
* FastAPI defines API endpoints using Python functions.
* Pydantic validates request bodies.
* In-memory storage is temporary and disappears when the server restarts.

---

### Day 2 — Improved Job API

Implemented:

* `GET /jobs`
* `GET /jobs?status_filter=pending`
* `PATCH /jobs/{job_id}/status`
* `POST /jobs/{job_id}/cancel`
* Job status enum
* Priority validation
* Response models
* Proper HTTP status codes

Learned:

* Path parameters identify specific resources.
* Query parameters are used for filtering/searching/sorting/pagination.
* `PATCH` updates part of an existing resource.
* Enums restrict values to a fixed set.
* `400` means logically invalid request.
* `404` means resource not found.
* `422` means validation failed.

---

### Day 3 — Clean Backend Structure

Refactored from one large `main.py` file into a cleaner backend structure.

Added:

```text
app/
  main.py
  models.py
  schemas.py
  services.py
  routes/
    jobs.py
```

Learned:

* `main.py` should create the app and include routers.
* `APIRouter` groups related endpoints.
* `schemas.py` stores request/response models.
* `services.py` stores business logic.
* Routes should handle HTTP behavior.
* Services should handle application logic.

---

### Day 4 — PostgreSQL Persistence

Replaced temporary in-memory job storage with PostgreSQL.

Added:

* PostgreSQL using Docker Compose
* SQLAlchemy setup
* `JobDB` database model
* Database session dependency using `get_db`
* Persistent job creation, listing, fetching, updating, and cancellation
* `created_at` and `updated_at` timestamps

Learned:

* PostgreSQL stores data permanently.
* SQLAlchemy ORM maps Python classes to database tables.
* A database session communicates with the database during a request.
* `db.add()` prepares an object for insertion.
* `db.commit()` saves changes.
* `db.refresh()` reloads saved database values into the Python object.

---

### Day 5 — Expanded Job Database Model

Upgraded the job database schema to support real queue features.

Added:

* `queue_name`
* `attempts`
* `max_retries`
* `run_at`
* `locked_by`
* `locked_at`
* `error_message`
* `completed_at`
* PostgreSQL `JSONB` payload storage

Learned:

* `queue_name` supports multiple queues.
* `run_at` supports delayed jobs.
* `attempts` and `max_retries` support retry logic.
* `locked_by` and `locked_at` support future worker crash recovery.
* `error_message` stores failure reason.
* `completed_at` records successful completion time.
* JSONB stores structured JSON payloads properly in PostgreSQL.

---

### Day 6 — Redis Queue Layer

Added Redis as the fast queue dispatch layer.

Implemented:

* Redis container in Docker Compose
* Redis Python client
* Ready queue using Redis sorted set
* Delayed queue using Redis sorted set
* Immediate jobs enqueued into `queue:{queue_name}:ready`
* Delayed jobs enqueued into `queue:{queue_name}:delayed`
* Priority-based score for ready jobs
* Timestamp-based score for delayed jobs

Learned:

* PostgreSQL stores full job data.
* Redis stores job IDs for fast queue ordering.
* Redis sorted sets order members by score.
* `ZADD` adds a member with a score.
* `ZRANGE ... WITHSCORES` shows queue order.
* Higher-priority jobs can be picked earlier by giving them lower scores.
* Delayed jobs can be ordered using `run_at` timestamps.

---

### Day 7 — Basic Worker Process

Added the first worker process for executing queued jobs.

Implemented:

* `worker.py` command-line worker
* Redis `ZPOPMIN` based ready queue popping
* Dummy task handlers:

  * `sleep_task`
  * `echo_task`
  * `fail_task`
* Job execution lifecycle:

  * `queued -> running -> done`
  * `queued -> running -> failed`
* PostgreSQL status updates from the worker
* Error tracking using `error_message`
* Completion tracking using `completed_at`

Learned:

* A worker is a separate long-running process.
* The API should submit jobs, not execute them.
* Redis stores the next job ID to process.
* PostgreSQL stores full job metadata and lifecycle state.
* `ZPOPMIN` removes and returns the next job from a Redis sorted set.
* Worker loads job details from PostgreSQL before execution.
* Successful jobs become `done`.
* Failed jobs become `failed`.

---

## Current Limitations

The system is not complete yet.

Current limitations:

* No scheduler for delayed jobs yet
* No automatic retry logic yet
* No dead-letter queue yet
* No worker concurrency yet
* No worker crash recovery yet
* No metrics endpoint yet
* No benchmark script yet
* No dashboard yet
* No Alembic migrations yet

---

## Planned Next Steps

Next major steps:

1. Add scheduler to move due delayed jobs into ready queue.
2. Add retry system with exponential backoff.
3. Add dead-letter queue for exhausted jobs.
4. Add worker leases using `locked_by` and `locked_at`.
5. Add crash recovery for stuck running jobs.
6. Add worker concurrency.
7. Add metrics endpoint.
8. Add benchmark script.
9. Add Docker Compose service definitions for API, worker, and scheduler.
10. Add final README architecture diagrams and resume-ready benchmark results.


---

### Day 8 — Delayed Job Scheduler

Added a scheduler process to move due delayed jobs into the ready queue.

Implemented:

- `scheduler.py` command-line scheduler
- Redis `ZRANGEBYSCORE` lookup for due delayed jobs
- Moving due jobs from `queue:{queue_name}:delayed` to `queue:{queue_name}:ready`
- Updating delayed job status from `pending` to `queued`
- End-to-end delayed execution with API, scheduler, worker, Redis, and PostgreSQL

Current scheduler command:

```bash
python scheduler.py --queue default --poll-interval 2
```

Delayed job flow:

```text
POST /jobs with delay_seconds > 0
  ↓
PostgreSQL stores job as pending
  ↓
Redis delayed queue stores job_id with run_at timestamp score
  ↓
scheduler.py finds job when run_at <= current_time
  ↓
scheduler moves job_id to ready queue
  ↓
worker.py picks job
  ↓
worker marks job running then done/failed
```

What I learned:

- Delayed jobs should not be executed immediately.
- Redis sorted set scores can represent future execution timestamps.
- `ZRANGEBYSCORE` can find jobs whose scheduled time has arrived.
- Scheduler is a separate long-running process.
- API, scheduler, and worker have separate responsibilities.

Current limitation:

- No retry scheduling yet.
- No dead-letter queue yet.
- No worker crash recovery yet.
- No concurrency yet.


---

### Day 9 — Retry System with Exponential Backoff

Added automatic retry scheduling for failed jobs.

Implemented:

- Retry-aware failure handling
- `attempts` increment on task failure
- `max_retries` based retry limit
- Exponential backoff retry delay
- Failed jobs reinserted into Redis delayed queue for future retry
- Scheduler moves retry jobs back into ready queue when due
- Worker retries jobs until success or retry limit is reached
- `unstable_task` for testing jobs that fail first and succeed later

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
    status = failed
```

Current retry delay:

```text
retry_delay = base_delay * 2^attempts
```

With base delay of 5 seconds:

```text
attempt 1 failure → retry after 10 seconds
attempt 2 failure → retry after 20 seconds
attempt 3 failure → retry after 40 seconds
```

What I learned:

- Some failures are temporary and should be retried.
- Retry logic needs attempt tracking.
- `max_retries` prevents infinite retry loops.
- Exponential backoff avoids retrying too aggressively.
- Retry scheduling can reuse the delayed queue mechanism.
- A job should only become finally failed after exhausting retries.

Current limitations:

- No dead-letter queue yet.
- No retry jitter yet.
- `unstable_task` uses in-memory simulation for testing.
- No worker crash recovery yet.