import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FaceGate"
    database_url: str = "sqlite:///./facegate.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    default_admin_username: str = "admin"
    default_admin_password: str = "SafeGate2026!"
    recognition_confidence_threshold: float = 70.0  # LBPH distance; LOWER = stricter match
    model_dir: str = "./face_models"
    max_upload_mb: int = 10
    allowed_image_types: str = "image/jpeg,image/png"

    class Config:
        env_file = ".env"


settings = Settings()
os.makedirs(settings.model_dir, exist_ok=True)
