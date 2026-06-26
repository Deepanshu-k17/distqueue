# DistQueue Architecture

DistQueue is a Redis-backed distributed task queue engine built with FastAPI, PostgreSQL, Redis, SQLAlchemy, and Python worker processes.

The system separates durable job state from fast queue dispatch.

## High-Level Flow

```text
Client
  ↓
FastAPI API
  ↓
PostgreSQL stores durable job metadata
  ↓
Redis stores job IDs for fast queue ordering
  ↓
Worker processes execute jobs
  ↓
Scheduler handles delayed jobs, retries, and stuck-job recovery
Core Components
API Server

The FastAPI server exposes endpoints for:

creating jobs
listing jobs
fetching job details
updating job status
cancelling jobs
listing dead-letter jobs
retrying dead jobs
reading queue metrics

The API does not execute jobs directly. It validates requests, stores metadata, and enqueues job IDs.

PostgreSQL

PostgreSQL is the durable source of truth.

It stores:

job ID
queue name
task type
payload
priority
status
attempts
max retries
run time
lock metadata
error message
timestamps

Even if Redis or workers restart, job metadata remains available.

Redis

Redis is used as the fast queue dispatch layer.

It stores only job IDs, not full job payloads.

Queues:

queue:default:ready
queue:default:delayed
queue:default:dead

Redis sorted sets are used because they allow jobs to be ordered by score.

Worker

The worker process pops job IDs from Redis ready queue, loads full job metadata from PostgreSQL, executes the task, and updates job status.

Worker lifecycle:

queued → running → done
queued → running → pending retry
queued → running → dead
Scheduler

The scheduler handles two responsibilities:

Moving due delayed/retry jobs into the ready queue.
Recovering stuck running jobs if worker leases expire.
Why PostgreSQL + Redis?

PostgreSQL gives durability and queryability.

Redis gives fast queue ordering and dispatch.

DistQueue uses both:

PostgreSQL = durable metadata
Redis = fast queue ordering
Priority Queue Design

Ready jobs are stored in Redis sorted sets.

Score formula:

score = (-priority * 1_000_000_000) + current_timestamp_ms

Higher priority jobs get lower scores and are popped earlier using ZPOPMIN.

Delayed Jobs

Delayed jobs are stored in Redis delayed queue using run_at timestamp as the score.

score = run_at_timestamp

Scheduler moves jobs when:

run_at <= current_time
Retry System

When a task fails:

attempts += 1

If retries remain:

status = pending
run_at = now + retry_delay
job_id goes to delayed queue

If retries are exhausted:

status = dead
job_id goes to dead-letter queue

Retry delay uses exponential backoff:

retry_delay = base_delay * 2^attempts
Worker Crash Recovery

When a worker starts a job:

status = running
locked_by = worker_id
locked_at = current_time

If the worker crashes, the job can remain stuck in running.

The scheduler detects stale locks:

locked_at < current_time - lock_timeout

Then it requeues the job:

status = queued
locked_by = null
locked_at = null
job_id goes back to ready queue

This prevents jobs from being stuck forever.
