import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AdminUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# Simple in-memory rate limiter for the login endpoint: max 5 attempts / 60s per IP.
_login_attempts: dict[str, list[float]] = {}


def check_rate_limit(request: Request, max_attempts: int = 5, window_seconds: int = 60):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    attempts = [t for t in _login_attempts.get(ip, []) if now - t < window_seconds]
    if len(attempts) >= max_attempts:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again shortly.")
    attempts.append(now)
    _login_attempts[ip] = attempts


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def ensure_default_admin(db: Session):
    existing = db.query(AdminUser).filter(AdminUser.username == settings.default_admin_username).first()
    if not existing:
        db.add(AdminUser(
            username=settings.default_admin_username,
            hashed_password=hash_password(settings.default_admin_password),
            role="admin",
        ))
        db.commit()
