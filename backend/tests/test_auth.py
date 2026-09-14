from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_login_success():
    r = client.post(
        "/api/auth/login",
        params={"username": settings.default_admin_username, "password": settings.default_admin_password},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_rejected():
    r = client.post("/api/auth/login", params={"username": settings.default_admin_username, "password": "wrong"})
    assert r.status_code == 401


def test_protected_route_requires_token():
    r = client.get("/api/enroll")
    assert r.status_code == 401


def test_rate_limit_blocks_after_many_attempts():
    for _ in range(5):
        client.post("/api/auth/login", params={"username": "x", "password": "y"})
    r = client.post("/api/auth/login", params={"username": "x", "password": "y"})
    assert r.status_code == 429
