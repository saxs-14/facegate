from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.auth import _login_attempts

client = TestClient(app)


def _token():
    _login_attempts.clear()  # avoid cross-test-module rate-limit interference
    r = client.post(
        "/api/auth/login",
        params={"username": settings.default_admin_username, "password": settings.default_admin_password},
    )
    return r.json()["access_token"]


def test_dashboard_summary_requires_auth():
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 401


def test_dashboard_summary_shape():
    token = _token()
    r = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    for key in ["total_enrolled", "total_events", "unknown_events", "events_today", "confidence_threshold"]:
        assert key in r.json()


def test_enroll_rejects_image_with_no_face():
    token = _token()
    import numpy as np
    import cv2

    blank = np.zeros((100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", blank)
    r = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {token}"},
        data={"name": "Test Person", "category": "visitor", "consent_given": "true"},
        files={"file": ("blank.jpg", buf.tobytes(), "image/jpeg")},
    )
    assert r.status_code == 422


def test_enroll_requires_consent():
    token = _token()
    import numpy as np
    import cv2

    blank = np.zeros((100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", blank)
    r = client.post(
        "/api/enroll",
        headers={"Authorization": f"Bearer {token}"},
        data={"name": "Test Person", "category": "visitor", "consent_given": "false"},
        files={"file": ("blank.jpg", buf.tobytes(), "image/jpeg")},
    )
    assert r.status_code == 400
