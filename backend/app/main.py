from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, SessionLocal
from app.auth import ensure_default_admin
from app.routers import health, auth_router, enroll, recognize, events

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    ensure_default_admin(db)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth_router.router)
app.include_router(enroll.router)
app.include_router(recognize.router)
app.include_router(events.router)


@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs"}
