import os
from datetime import date, timedelta
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
from app.ml.train_candidate import _prepare_dataset, train_candidate_from_frame
import app.api as api_module


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
    monitoring = client.get("/api/admin/model-monitoring", headers=admin_headers)
    assert monitoring.status_code == 200
    assert monitoring.json()["status"] in {"insufficient_data", "exploratory"}
    assert client.get("/api/admin/teaching-staff", headers=admin_headers).status_code == 200

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
    intelligence = client.get("/api/teacher/intelligence", headers=teacher_headers)
    assert intelligence.status_code == 200
    assert intelligence.json()["assigned_student_count"] == 1
    assert intelligence.json()["assigned_students"][0]["student_id"] == student_id

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
    aggregate = client.get("/api/institution/intelligence", headers=institution_headers)
    assert aggregate.status_code == 200
    assert aggregate.json()["student_count"] >= 1
    assert "assigned_students" not in aggregate.json()
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



def test_student_activity_tracking_is_validated_and_owner_scoped():
    first = client.post("/api/auth/register", json={
        "full_name": "Activity Owner", "email": "activity-owner@example.com",
        "password": "StrongPassword123", "confirm_password": "StrongPassword123",
    })
    headers = {"Authorization": f"Bearer {first.json()['access_token']}"}
    study = client.post("/api/student/activities", headers=headers, json={
        "activity_type": "study_session", "subject": "Physics",
        "value": 2.5, "occurred_on": "2026-11-20",
    })
    assert study.status_code == 201
    attendance = client.post("/api/student/activities", headers=headers, json={
        "activity_type": "attendance", "subject": "Physics",
        "value": 1, "occurred_on": "2026-11-20",
    })
    assert attendance.status_code == 201
    assignment = client.post("/api/student/activities", headers=headers, json={
        "activity_type": "assignment", "subject": "Physics",
        "value": 82, "occurred_on": "2026-11-20",
    })
    assert assignment.status_code == 201

    invalid_attendance = client.post("/api/student/activities", headers=headers, json={
        "activity_type": "attendance", "subject": "Physics",
        "value": 75, "occurred_on": "2026-11-20",
    })
    assert invalid_attendance.status_code == 422

    summary = client.get("/api/student/activities/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["study_hours_last_7_days"] == 2.5
    assert summary.json()["recorded_attendance_percentage"] == 100
    assert summary.json()["average_assignment_score"] == 82

    other = client.post("/api/auth/register", json={
        "full_name": "Other Activity User", "email": "activity-other@example.com",
        "password": "StrongPassword123", "confirm_password": "StrongPassword123",
    })
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert client.delete(
        f"/api/student/activities/{study.json()['id']}", headers=other_headers
    ).status_code == 404



def test_semester_analytics_are_scoped_to_authenticated_student():
    registered = client.post("/api/auth/register", json={
        "full_name": "Analytics Student", "email": "semester-analytics@example.com",
        "password": "StrongPassword123", "confirm_password": "StrongPassword123",
    })
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    base = {
        "subject": "Physics", "semester": "1", "study_hours": 4,
        "previous_marks": 70, "attendance": 85, "assignment_scores": 75,
        "class_participation": 70, "homework_completion": 80,
        "sleep_hours": 7, "extracurricular": False,
        "internet_access": True, "family_support": True,
    }
    assert client.post("/api/predictions/predict", headers=headers, json=base).status_code == 200
    next_semester = {**base, "semester": "2", "subject": "Chemistry"}
    assert client.post("/api/predictions/predict", headers=headers, json=next_semester).status_code == 200

    heatmap = client.get("/api/analytics/heatmap", headers=headers)
    assert heatmap.status_code == 200
    assert len(heatmap.json()) == 2
    comparison = client.get("/api/analytics/semester-comparison", headers=headers)
    assert comparison.status_code == 200
    assert {item["semester"] for item in comparison.json()} == {"1", "2"}



def test_external_assistant_provider_requires_explicit_per_request_consent(monkeypatch):
    registered = client.post("/api/auth/register", json={
        "full_name": "Consent Student", "email": "consent@example.com",
        "password": "StrongPassword123", "confirm_password": "StrongPassword123",
    })
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    monkeypatch.setenv("AI_API_KEY", "test-only-provider-key")
    monkeypatch.setenv("AI_MODEL", "test-model")
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "Use short focused study sessions."}}]}

    def fake_post(url, headers, json, timeout):
        calls.append(json)
        return FakeResponse()

    monkeypatch.setattr(api_module.httpx, "post", fake_post)
    fallback = client.post("/api/assistant/chat", headers=headers, json={
        "question": "How should I study?",
    })
    assert fallback.status_code == 200
    assert fallback.json()["provider"] == "built_in_contextual_fallback"
    assert calls == []

    consented = client.post("/api/assistant/chat", headers=headers, json={
        "question": "How should I study?", "allow_external_processing": True,
    })
    assert consented.status_code == 200
    assert consented.json()["provider"] == "configured_llm"
    assert len(calls) == 1
    assert "student_name" not in calls[0]["messages"][1]["content"]
    assert "latest_prediction_id" not in calls[0]["messages"][1]["content"]



def test_candidate_training_supports_grouped_student_records():
    frame = synthetic_training_frame(rows=300)
    frame["student_group"] = [f"student-{index // 3}" for index in range(300)]
    artifact, report = train_candidate_from_frame(
        frame, target_column="score", source_fingerprint="grouped-test-data",
        group_column="student_group",
    )
    assert report["quality"]["unique_groups"] == 100
    assert "GroupShuffleSplit" in report["split"]["strategy"]
    assert artifact["training_rows"] + artifact["test_rows"] == 300
    assert report["split"]["groups_disjoint"] is True
    assert report["split"]["group_count_train"] >= 5
    assert report["split"]["group_count_test"] >= 1
    assert len(report["candidate_comparison"]) == 4
    assert all(item["cross_validation_fold_count"] == 5 for item in report["candidate_comparison"])
    assert report["held_out_test_metrics"]["mae"] >= 0
    assert report["mean_baseline_test_metrics"]["mae"] >= 0
    assert "mae_improvement_over_mean_baseline_percent" in report
    assert report["quality"]["target_summary"]["minimum"] >= 0
    assert report["quality"]["target_summary"]["maximum"] <= 100
    assert report["quality"]["correlation_audit"]["interpretation"]
    assert artifact["feature_schema_version"] == "1.0"
    assert artifact["scikit_learn_version"]


def test_candidate_dataset_audit_counts_duplicates_and_missing_rows():
    frame = synthetic_training_frame(rows=180)
    frame = pd.concat(
        [frame, frame.iloc[[0]], frame.iloc[[1]].assign(study_hours=np.nan)],
        ignore_index=True,
    )
    _, _, quality, _ = _prepare_dataset(frame, target_column="score")
    assert quality["source_rows"] == 182
    assert quality["duplicate_rows_removed"] == 1
    assert quality["incomplete_rows_removed"] == 1
    assert quality["valid_rows"] == 180
    assert quality["missing_values_by_column_before_cleaning"]["study_hours"] == 1
    assert len(quality["feature_summary"]) == 10


def test_candidate_dataset_rejects_invalid_boolean_and_target_feature_overlap():
    frame = synthetic_training_frame(rows=180)
    invalid_boolean = frame.copy()
    invalid_boolean.loc[0, "internet_access"] = "sometimes"
    with pytest.raises(ValueError, match="unsupported values"):
        train_candidate_from_frame(invalid_boolean, source_fingerprint="invalid-boolean")

    with pytest.raises(ValueError, match="target column cannot also"):
        train_candidate_from_frame(frame, target_column="study_hours")


def test_candidate_group_column_must_not_be_a_model_feature():
    frame = synthetic_training_frame(rows=180)
    with pytest.raises(ValueError, match="grouping column must be separate"):
        train_candidate_from_frame(
            frame, target_column="score", group_column="study_hours"
        )


def test_extended_student_growth_lab_endpoints():
    registration = client.post("/api/auth/register", json={
        "full_name": "Growth Lab Student", "email": "growth-lab@example.com",
        "password": "StrongPassword123", "confirm_password": "StrongPassword123",
        "institution_name": "Growth University", "course": "Computer Science",
        "semester": "5",
    })
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}

    no_auth = client.get("/api/student/digital-twin")
    assert no_auth.status_code == 401

    prediction = client.post("/api/predictions/predict", headers=headers, json={
        "subject": "Mathematics", "semester": "5", "study_hours": 1.5,
        "previous_marks": 48, "attendance": 62, "assignment_scores": 52,
        "class_participation": 65, "homework_completion": 55, "sleep_hours": 7,
        "extracurricular": False, "internet_access": True, "family_support": True,
    })
    assert prediction.status_code == 200

    twin = client.get("/api/student/digital-twin", headers=headers)
    assert twin.status_code == 200
    assert twin.json()["status"] == "initialized"
    assert twin.json()["latest_assessment"]["prediction_id"] == prediction.json()["id"]
    assert twin.json()["timeline"]

    recovery = client.get("/api/student/recovery-plan", headers=headers)
    assert recovery.status_code == 200
    assert recovery.json()["status"] == "generated"
    assert len(recovery.json()["weeks"]) == 4

    exam = client.post("/api/student/exam-preparation", headers=headers, json={
        "subject": "Mathematics",
        "exam_date": (date.today() + timedelta(days=3)).isoformat(),
        "hours_per_day": 2,
        "topics": ["Algebra", "Calculus"],
    })
    assert exam.status_code == 200
    assert len(exam.json()["schedule"]) == 4

    invalid_exam = client.post("/api/student/exam-preparation", headers=headers, json={
        "subject": "Mathematics", "exam_date": (date.today() - timedelta(days=1)).isoformat(),
        "topics": ["Algebra"],
    })
    assert invalid_exam.status_code == 422

    questions = client.post("/api/student/question-generator", headers=headers, json={
        "subject": "Computer Science", "topic": "Database normalization",
        "difficulty": "hard", "count": 4,
    })
    assert questions.status_code == 200
    assert len(questions.json()["questions"]) == 4
    assert "not questions from a real" in questions.json()["notice"]

    career = client.post("/api/student/career-readiness", headers=headers, json={
        "target_role": "AI/ML Engineer",
        "skills": ["Python", "Machine Learning", "Pandas"],
        "projects_count": 2, "internship_experience": False, "portfolio_ready": True,
    })
    assert career.status_code == 200
    assert career.json()["skill_coverage_percentage"] > 0
    assert career.json()["suggested_skill_gaps"]

    scholarships = client.post("/api/student/scholarship-matches", headers=headers, json={
        "academic_percentage": 82, "course_area": "Information Technology",
        "annual_income_band": "undisclosed", "state": "Karnataka",
    })
    assert scholarships.status_code == 200
    pathways = [item["pathway"] for item in scholarships.json()["potential_pathways"]]
    assert "Merit-based scholarships" in pathways
    assert "State and domicile-based schemes" in pathways
    assert "not a list of verified live awards" in scholarships.json()["disclaimer"]

    # Student accounts cannot access staff-only intelligence endpoints.
    assert client.get("/api/teacher/intelligence", headers=headers).status_code == 403
    assert client.get("/api/institution/intelligence", headers=headers).status_code == 403
