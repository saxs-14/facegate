from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from datetime import datetime, timezone
from app.database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="admin")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EnrolledPerson(Base):
    __tablename__ = "enrolled_persons"

    id = Column(Integer, primary_key=True)
    label_id = Column(Integer, unique=True, index=True)  # numeric label used internally by LBPH
    name = Column(String)
    category = Column(String, default="visitor")  # visitor | staff
    consent_given = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AccessEvent(Base):
    __tablename__ = "access_events"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, nullable=True)
    recognized_name = Column(String, nullable=True)
    confidence_distance = Column(Float)  # LBPH distance - lower is a better match
    event_type = Column(String)  # check_in | check_out | unknown
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor = Column(String)
    action = Column(String)
    target = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
