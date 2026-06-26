# Current Limitations

DistQueue is a learning-focused distributed task queue engine prototype. It implements the core concepts of a job queue, but it is not production-grade yet.

## Limitations

### No Alembic Migrations

The project currently uses:

```python
Base.metadata.create_all(bind=engine)

This is acceptable for development, but production systems should use migrations through Alembic.

No Strong Idempotency Guarantee

If a worker crashes after partially executing a task, the scheduler may requeue the job. This means the task could execute more than once.

Production systems need idempotent task design or deduplication.

Basic Metrics Only

The metrics endpoint provides queue depth, status counts, and average latency.

It does not yet provide:

p50 latency
p95 latency
p99 latency
throughput over time
time-series monitoring
No Dashboard

There is no UI dashboard yet. Monitoring is through API endpoints, logs, Redis CLI, PostgreSQL queries, and scripts.

Simple Retry Strategy

Retries use exponential backoff, but there is no jitter yet.

Production systems often add jitter to avoid thundering herd retry bursts.

Thread-Based Concurrency

Worker concurrency uses Python ThreadPoolExecutor.

This is good for I/O-bound tasks, but not ideal for CPU-heavy tasks because of Python's GIL.

Basic Crash Recovery

Crash recovery is based on locked_at timeout.

It can recover stuck jobs, but it does not include worker heartbeats yet.

No Authentication

The API currently has no authentication or authorization.

No Rate Limiting

The API does not currently limit job submission rate.

No Horizontal Deployment Setup

The project can run multiple worker threads and Docker services locally, but it does not include Kubernetes or production deployment configuration.

Future Improvements
Add Alembic migrations
Add task idempotency keys
Add retry jitter
Add p50/p95/p99 metrics endpoint
Add dashboard
Add authentication
Add rate limiting
Add structured logging
Add pytest test suite
Add Kubernetes deployment examples
