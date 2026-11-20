import os
import pandas as pd
import pytest

os.environ["DATABASE_URL"] = "sqlite:///./test_student_performance.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["FRONTEND_URL"] = (
    "https://student-performance-prediction-amber.vercel.app,"
    "http://localhost:5173,http://127.0.0.1:5173"
)

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User
from app.core.security import hash_password
from app.ml.predictor import synthetic_training_frame
from app.ml.train_candidate import train_candidate_from_frame


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health_and_model_training():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    ready = client.get("/api/health/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"]["database"] == "available"
    assert ready.json()["checks"]["model"] == "available"


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

    recommendation_response = client.get("/api/recommendations", headers=headers)
    assert recommendation_response.status_code == 200
    assert recommendation_response.json() == body["recommendations"]
    assert recommendation_response.json()

    history = client.get("/api/predictions/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["total"] == 1

    student_detail = client.get(f"/api/predictions/{body['id']}", headers=headers)
    assert student_detail.status_code == 200

    explanation = client.get(
        f"/api/predictions/{body['id']}/explanation", headers=headers
    )
    assert explanation.status_code == 200
    explanation_body = explanation.json()
    assert explanation_body["model_version"] == body["model_version"]
    assert explanation_body["is_causal"] is False
    assert len(explanation_body["contributions"]) == 10
    reconstructed = explanation_body["baseline_score"] + sum(
        item["contribution"] for item in explanation_body["contributions"]
    )
    assert abs(reconstructed - explanation_body["raw_model_output"]) < 0.01

    baseline_input = body["input_data"]
    scenario_input = {**baseline_input, "study_hours": 7}
    simulation = client.post(
        "/api/predictions/simulate",
        headers=headers,
        json={"baseline": baseline_input, "scenario": scenario_input},
    )
    assert simulation.status_code == 200
    assert simulation.json()["saved"] is False
    assert simulation.json()["model_version"] == body["model_version"]
    assert simulation.json()["scenario_score"] >= 0
    assert client.get("/api/predictions/history", headers=headers).json()["total"] == 1

    other_user = client.post("/api/auth/register", json={
        "full_name": "Other Student",
        "email": "other-student@example.com",
        "password": "StrongPassword123",
        "confirm_password": "StrongPassword123",
    })
    other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}
    assert client.get(
        f"/api/predictions/{body['id']}", headers=other_headers
    ).status_code == 404
    assert client.delete(
        f"/api/predictions/{body['id']}", headers=other_headers
    ).status_code == 404
    assert client.get(
        f"/api/predictions/{body['id']}/explanation", headers=other_headers
    ).status_code == 404


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


def test_vercel_and_local_vite_origins_are_allowed_by_cors():
    for origin in [
        "https://student-performance-prediction-amber.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]:
        response = client.options(
            "/api/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "POST" in response.headers["access-control-allow-methods"]
        allowed_headers = response.headers["access-control-allow-headers"].lower()
        assert "authorization" in allowed_headers
        assert "content-type" in allowed_headers


def test_cors_does_not_allow_unlisted_origins():
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://unlisted.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert "access-control-allow-origin" not in response.headers



def test_academic_intelligence_goals_notifications_and_assistant():
    register = client.post("/api/auth/register", json={
        "full_name": "Planner Student",
        "email": "planner@example.com",
        "password": "StrongPassword123",
        "confirm_password": "StrongPassword123",
        "institution_name": "Test University",
    })
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    empty_risk = client.get("/api/student/risk-assessment", headers=headers)
    assert empty_risk.status_code == 200
    assert empty_risk.json()["status"] == "insufficient_data"

    no_plan = client.post("/api/student/study-plan", headers=headers, json={
        "available_hours_per_day": 2,
    })
    assert no_plan.status_code == 409

    prediction = client.post("/api/predictions/predict", headers=headers, json={
        "subject": "Mathematics", "semester": "3", "study_hours": 1,
        "previous_marks": 42, "attendance": 58, "assignment_scores": 38,
        "class_participation": 60, "homework_completion": 55,
        "sleep_hours": 7, "extracurricular": False,
        "internet_access": True, "family_support": True,
    })
    assert prediction.status_code == 200

    risk = client.get("/api/student/risk-assessment", headers=headers)
    assert risk.status_code == 200
    assert risk.json()["risk_level"] == "high"
    assert risk.json()["risk_points"] >= 4
    assert "probability" in risk.json()["risk_scale"]

    plan = client.post("/api/student/study-plan", headers=headers, json={
        "available_hours_per_day": 2.5, "focus_subject": "Mathematics",
    })
    assert plan.status_code == 200
    assert len(plan.json()["days"]) == 7
    assert plan.json()["subject"] == "Mathematics"

    goal = client.post("/api/student/goals", headers=headers, json={
        "title": "Revise algebra", "subject": "Mathematics",
    })
    assert goal.status_code == 201
    goal_id = goal.json()["id"]
    assert client.get("/api/student/goals", headers=headers).json()[0]["id"] == goal_id
    updated = client.patch(f"/api/student/goals/{goal_id}", headers=headers, json={
        "status": "completed",
    })
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"
    assert client.delete(f"/api/student/goals/{goal_id}", headers=headers).status_code == 204

    notifications = client.get("/api/student/notifications", headers=headers)
    assert notifications.status_code == 200
    assert isinstance(notifications.json(), list)

    assistant = client.post("/api/assistant/chat", headers=headers, json={
        "question": "How can I improve my attendance?",
    })
    assert assistant.status_code == 200
    assert assistant.json()["provider"] == "built_in_contextual_fallback"
    assert "58.0%" in assistant.json()["answer"]


def test_teacher_portal_assignment_isolation_and_institution_analytics():
    db = SessionLocal()
    try:
        admin = User(
            full_name="Test Admin", email="portal-admin@example.com",
            password_hash=hash_password("AdminPassword123!"),
            role="admin", institution_name="Test University",
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()

    admin_login = client.post("/api/auth/login", json={
        "email": "portal-admin@example.com", "password": "AdminPassword123!",
    })
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    student_response = client.post("/api/auth/register", json={
        "full_name": "Assigned Student", "email": "assigned@example.com",
        "password": "StrongPassword123", "confirm_password": "StrongPassword123",
        "institution_name": "Test University",
    })
    student_id = student_response.json()["user"]["id"]

    teacher_response = client.post("/api/admin/teachers", headers=admin_headers, json={
        "full_name": "Assigned Teacher", "email": "teacher@example.com",
        "password": "TeacherPassword123!", "institution_name": "Test University",
    })
    assert teacher_response.status_code == 201
    teacher_id = teacher_response.json()["id"]

    assignment = client.post(
        f"/api/admin/teachers/{teacher_id}/assignments",
        headers=admin_headers, json={"student_id": student_id},
    )
    assert assignment.status_code == 201

    teacher_login = client.post("/api/auth/login", json={
        "email": "teacher@example.com", "password": "TeacherPassword123!",
    })
    teacher_headers = {"Authorization": f"Bearer {teacher_login.json()['access_token']}"}
    dashboard = client.get("/api/teacher/dashboard", headers=teacher_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["assigned_students"] == 1

    note = client.post("/api/teacher/interventions", headers=teacher_headers, json={
        "student_id": student_id, "note": "Discuss a weekly revision plan.",
    })
    assert note.status_code == 201
    assert client.get(
        f"/api/teacher/students/{student_id}/interventions",
        headers=teacher_headers,
    ).status_code == 200

    unassigned = client.post("/api/teacher/interventions", headers=teacher_headers, json={
        "student_id": student_id + 9999, "note": "Unauthorized note",
    })
    assert unassigned.status_code == 404
    assert client.get("/api/admin/dashboard", headers=teacher_headers).status_code == 403

    institution_response = client.post(
        "/api/admin/institution-admins", headers=admin_headers, json={
            "full_name": "Institution Admin", "email": "institution@example.com",
            "password": "InstitutionPassword123!",
            "institution_name": "Test University",
        },
    )
    assert institution_response.status_code == 201
    institution_login = client.post("/api/auth/login", json={
        "email": "institution@example.com", "password": "InstitutionPassword123!",
    })
    institution_headers = {"Authorization": f"Bearer {institution_login.json()['access_token']}"}
    analytics = client.get("/api/institution/analytics", headers=institution_headers)
    assert analytics.status_code == 200
    assert analytics.json()["student_count"] >= 1
    assert client.get("/api/teacher/dashboard", headers=institution_headers).status_code == 403



def test_candidate_training_compares_models_without_replacing_live_artifact():
    frame = synthetic_training_frame(rows=300)
    artifact, report = train_candidate_from_frame(
        frame, target_column="score", source_fingerprint="unit-test-dataset",
    )
    assert artifact["version"].startswith("candidate-")
    assert artifact["training_rows"] + artifact["test_rows"] == 300
    assert report["selected_model"] in {
        "ridge", "random_forest", "gradient_boosting", "hist_gradient_boosting",
    }
    assert len(report["candidate_comparison"]) == 4
    assert report["held_out_test_metrics"]["mae"] >= 0
    assert "live model" in " ".join(report["limitations"]).lower()


def test_candidate_training_rejects_missing_features_and_small_datasets():
    from app.ml.train_candidate import train_candidate_from_frame

    with pytest.raises(ValueError, match="missing required columns"):
        train_candidate_from_frame(pd.DataFrame({"score": [50] * 120}))
    with pytest.raises(ValueError, match="At least 100"):
        train_candidate_from_frame(synthetic_training_frame(rows=50))
