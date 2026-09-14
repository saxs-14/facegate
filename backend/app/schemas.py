from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PersonOut(BaseModel):
    id: int
    name: str
    category: str
    consent_given: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AccessEventOut(BaseModel):
    id: int
    person_id: Optional[int]
    recognized_name: Optional[str]
    confidence_distance: float
    event_type: str
    timestamp: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_enrolled: int
    total_events: int
    unknown_events: int
    events_today: int
    confidence_threshold: float
