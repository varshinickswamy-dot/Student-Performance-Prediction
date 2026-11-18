import os

os.environ["DATABASE_URL"] = "sqlite:///./test_student_performance.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health_and_model_training():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_registration_login_prediction_and_history():
    register = client.post("/api/auth/register", json={
        "full_name": "Test Student",
        "email": "student@example.com",
        "password": "StrongPassword123",
        "confirm_password": "StrongPassword123",
        "institution_name": "Test University",
    })
    assert register.status_code == 201
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    prediction = client.post("/api/predictions/predict", headers=headers, json={
        "subject": "Mathematics",
        "semester": "2",
        "study_hours": 5,
        "previous_marks": 72,
        "attendance": 88,
        "assignment_scores": 76,
        "class_participation": 70,
        "homework_completion": 82,
        "sleep_hours": 7.5,
        "extracurricular": True,
        "internet_access": True,
        "family_support": True,
    })
    assert prediction.status_code == 200
    body = prediction.json()
    assert 0 <= body["predicted_score"] <= 100
    assert body["performance_category"] in {"Excellent", "Good", "Average", "Needs Improvement"}

    history = client.get("/api/predictions/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["total"] == 1

    student_detail = client.get(f"/api/predictions/{body['id']}", headers=headers)
    assert student_detail.status_code == 200


def test_admin_role_is_enforced():
    register = client.post("/api/auth/register", json={
        "full_name": "Regular Student",
        "email": "regular@example.com",
        "password": "StrongPassword123",
        "confirm_password": "StrongPassword123",
    })
    token = register.json()["access_token"]
    response = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_password_reset_request_is_honest_without_email_provider():
    response = client.post(
        "/api/auth/password-reset/request",
        json={"email": "student@example.com"},
    )
    assert response.status_code == 503


def test_local_vite_origins_are_allowed_by_cors():
    for origin in ["http://localhost:5173", "http://127.0.0.1:5173"]:
        response = client.options(
            "/api/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
