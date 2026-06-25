from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.database import get_db

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
def get_metrics(
    queue: str = "default",
    db: Session = Depends(get_db),
):
    return services.get_queue_metrics(db, queue)