from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import cv2
import numpy as np

from app.database import get_db
from app.models import EnrolledPerson, AccessEvent, AdminUser
from app.schemas import AccessEventOut
from app.auth import get_current_admin
from app.config import settings
from app.face_engine import largest_face_patch, recognize_face

router = APIRouter(prefix="/api/recognize", tags=["recognize"])


@router.post("", response_model=AccessEventOut)
async def recognize(
    event_type: str = Form(default="check_in"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    if event_type not in ("check_in", "check_out"):
        raise HTTPException(status_code=400, detail="event_type must be check_in or check_out")
    if file.content_type not in settings.allowed_image_types.split(","):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    img_array = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    patch = largest_face_patch(frame)
    if patch is None:
        raise HTTPException(status_code=422, detail="No face detected in the uploaded image")

    label_id, distance = recognize_face(patch)

    person = None
    if label_id is not None:
        person = db.query(EnrolledPerson).filter(EnrolledPerson.label_id == label_id).first()

    event = AccessEvent(
        person_id=person.id if person else None,
        recognized_name=person.name if person else None,
        confidence_distance=round(float(distance), 1),
        event_type=event_type if person else "unknown",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
