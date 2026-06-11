from fastapi import FastAPI

from app.routes import jobs

app = FastAPI(title="DistQueue")


@app.get("/")
def root():
    return {
        "message": "DistQueue API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


app.include_router(jobs.router)