from fastapi import FastAPI

from app import db_models
from app.database import Base, engine
from app.routes import jobs, metrics

Base.metadata.create_all(bind=engine)

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
app.include_router(metrics.router)