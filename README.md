# DistQueue

DistQueue is a distributed task queue engine project. The final goal is to build a Redis-backed job queue system with FastAPI, PostgreSQL, Redis, worker processes, scheduling, retries, dead-letter queues, crash recovery, metrics, and benchmarking.

This project is being built step by step to understand backend systems properly, instead of directly jumping into a large copy-pasted system.

---

## Current Status

Implemented a simple FastAPI backend with in-memory job storage.

Features added:

- `GET /`
- `GET /health`
- `POST /jobs`
- `GET /jobs/{job_id}`
- Temporary in-memory storage using a Python dictionary

What was learned:

- Backend receives HTTP requests and returns HTTP responses.
- `GET` is used to fetch/read data from the server.
- `POST` is used when the client sends data to the server to create something or perform an action.
- JSON is used to send structured data between client and server.
- FastAPI uses Python functions to define API endpoints.
- Pydantic validates incoming request bodies.
- In-memory storage is temporary and disappears when the server restarts.

---


Improved the basic API into a more realistic job-management API.

Features added:

- `GET /jobs` to list all jobs
- `GET /jobs?status_filter=pending` to filter jobs by status
- `PATCH /jobs/{job_id}/status` to update job status
- `POST /jobs/{job_id}/cancel` to cancel a job
- Job status enum
- Priority validation from 1 to 10
- Response models
- Proper HTTP status codes like `201`, `400`, `404`, and `422`

What was learned:

- A path parameter is a value inside the URL path used to identify a specific resource.
  - Example: `/jobs/job_123`
- A query parameter is an optional value after `?` in the URL, usually used for filtering, searching, sorting, or pagination.
  - Example: `/jobs?status_filter=pending`
- `PATCH` is used to update part of an existing resource.
- Enums restrict values to a fixed allowed set.
- Backend validation prevents invalid input from entering the system.
- `400 Bad Request` means the request is logically invalid.
- `404 Not Found` means the requested resource does not exist.
- `422 Unprocessable Entity` means the request format was valid JSON, but the data failed validation.

---

## Current API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Check if the API is running |
| `GET` | `/health` | Health check endpoint |
| `POST` | `/jobs` | Create a new job |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/jobs?status_filter=pending` | List jobs filtered by status |
| `GET` | `/jobs/{job_id}` | Get a specific job |
| `PATCH` | `/jobs/{job_id}/status` | Update job status |
| `POST` | `/jobs/{job_id}/cancel` | Cancel a job |

---

## Example Job Creation Request

```json
{
  "task_type": "sleep_task",
  "payload": {
    "seconds": 5
  },
  "priority": 8
}

---

### Day 3 — Clean Backend Structure

Refactored the FastAPI app from one large `main.py` file into a cleaner backend structure.

Added structure:

```text
app/
  main.py
  models.py
  schemas.py
  services.py
  routes/
    jobs.py---


Refactored the FastAPI app from one large `main.py` file into a cleaner backend structure.

Added structure:

```text
app/
  main.py
  models.py
  schemas.py
  services.py
  routes/
    jobs.py

What each file does:

main.py starts the FastAPI app and includes routers.
models.py contains internal domain models like job status.
schemas.py contains Pydantic request and response schemas.
services.py contains business logic for creating, listing, updating, and cancelling jobs.
routes/jobs.py contains HTTP API endpoints for job operations.

What I learned:

Real backend projects should not keep all logic inside main.py.
APIRouter helps split APIs into separate route files.
Routes should handle HTTP-specific behavior.
Services should handle business logic.
Schemas define the shape of input and output data.
This separation will make it easier to add PostgreSQL and Redis later.