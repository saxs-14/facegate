from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import cv2
import numpy as np

from app.database import get_db
from app.models import EnrolledPerson, AuditLog, AdminUser
from app.schemas import PersonOut
from app.auth import get_current_admin
from app.config import settings
from app.face_engine import largest_face_patch, enroll_face
from typing import List

router = APIRouter(prefix="/api/enroll", tags=["enroll"])


@router.get("", response_model=List[PersonOut])
def list_enrolled(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    return db.query(EnrolledPerson).order_by(EnrolledPerson.created_at.desc()).all()


@router.post("", response_model=PersonOut)
async def enroll(
    name: str = Form(...),
    category: str = Form(default="visitor"),
    consent_given: bool = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    if not consent_given:
        raise HTTPException(status_code=400, detail="Enrollment requires explicit consent (consent_given=true)")
    if file.content_type not in settings.allowed_image_types.split(","):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    img_array = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    patch = largest_face_patch(frame)
    if patch is None:
        raise HTTPException(status_code=422, detail="No face detected in the uploaded image")

    max_label = db.query(func.max(EnrolledPerson.label_id)).scalar() or 0
    next_label = max_label + 1

    person = EnrolledPerson(label_id=next_label, name=name, category=category, consent_given=True)
    db.add(person)
    db.commit()
    db.refresh(person)

    enroll_face(patch, next_label)

    db.add(AuditLog(actor=admin.username, action="enroll", target=f"person:{person.id} ({name})"))
    db.commit()

    return person


@router.delete("/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Right-to-erasure: removes the enrollment record. The person's face data
    remains folded into the trained LBPH model file until the next full
    re-train (documented limitation - see README 'Privacy considerations')."""
    person = db.query(EnrolledPerson).filter(EnrolledPerson.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.delete(person)
    db.add(AuditLog(actor=admin.username, action="delete", target=f"person:{person_id} ({person.name})"))
    db.commit()
    return {"deleted": True}
