import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import AccessEvent, EnrolledPerson
from app.schemas import AccessEventOut, DashboardSummary
from app.config import settings

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events", response_model=List[AccessEventOut])
def list_events(limit: int = 200, db: Session = Depends(get_db)):
    return db.query(AccessEvent).order_by(AccessEvent.timestamp.desc()).limit(limit).all()


@router.get("/events/export")
def export_events(db: Session = Depends(get_db)):
    events = db.query(AccessEvent).order_by(AccessEvent.timestamp.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "person_id", "recognized_name", "confidence_distance", "event_type", "timestamp"])
    for e in events:
        writer.writerow([e.id, e.person_id, e.recognized_name, e.confidence_distance, e.event_type, e.timestamp])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=facegate_events.csv"},
    )


@router.get("/dashboard/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    total_enrolled = db.query(func.count(EnrolledPerson.id)).scalar() or 0
    total_events = db.query(func.count(AccessEvent.id)).scalar() or 0
    unknown_events = db.query(func.count(AccessEvent.id)).filter(AccessEvent.event_type == "unknown").scalar() or 0
    today = datetime.now(timezone.utc).date()
    events_today = (
        db.query(func.count(AccessEvent.id))
        .filter(func.date(AccessEvent.timestamp) == str(today))
        .scalar()
        or 0
    )
    return DashboardSummary(
        total_enrolled=total_enrolled,
        total_events=total_events,
        unknown_events=unknown_events,
        events_today=events_today,
        confidence_threshold=settings.recognition_confidence_threshold,
    )
