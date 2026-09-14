from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdminUser
from app.schemas import Token
from app.auth import verify_password, create_access_token, check_rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(request: Request, username: str, password: str, db: Session = Depends(get_db)):
    check_rate_limit(request)
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.username, user.role)
    return Token(access_token=token)
