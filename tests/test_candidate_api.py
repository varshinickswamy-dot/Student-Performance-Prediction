from app.ml import student_candidate_inference as inference
from test_api import client


def test_final_exam_candidate_endpoint_requires_authentication_and_candidate_configuration(monkeypatch):
    monkeypatch.delenv("EDUPREDICT_STUDENT_CANDIDATE_ARTIFACT", raising=False)
    payload = {
        "attendance_pct": 80, "study_hours_per_week": 12, "sleep_hours": 7,
        "previous_sgpa": 8, "backlogs": 0, "internal_test_1": 40,
        "internal_test_2": 42, "assignment_score": 18,
        "extracurricular": True, "internet_access": True,
    }
    assert client.post("/api/student/final-exam-prediction", json=payload).status_code == 401
    registration = client.post("/api/auth/register", json={
        "full_name": "Candidate API Student", "email": "candidate-api@example.com",
        "password": "StrongPassword123", "confirm_password": "StrongPassword123",
    })
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    response = client.post("/api/student/final-exam-prediction", headers=headers, json=payload)
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
    invalid = client.post("/api/student/final-exam-prediction", headers=headers,
                          json={**payload, "attendance_pct": 120})
    assert invalid.status_code == 422


def test_final_exam_candidate_inference_returns_synthetic_labeled_estimate(monkeypatch):
    class FakePipeline:
        def predict(self, frame):
            assert list(frame.columns) == inference.EXPECTED_FEATURES
            assert len(frame) == 1
            return [87.25]

    monkeypatch.setattr(inference, "get_candidate", lambda: {
        "pipeline": FakePipeline(), "version": "synthetic-final-exam-test",
        "model_type": "ridge", "target": "final_exam_score",
        "dataset_provenance": "synthetic_anonymized_demonstration_dataset",
        "metrics": {"mae": 7.8, "rmse": 9.5, "r2": 0.59},
    })
    result = inference.predict_final_exam_score({
        "attendance_pct": 80, "study_hours_per_week": 12, "sleep_hours": 7,
        "previous_sgpa": 8, "backlogs": 0, "internal_test_1": 40,
        "internal_test_2": 42, "assignment_score": 18,
        "extracurricular": True, "internet_access": True,
    })
    assert result["predicted_final_exam_score"] == 87.25
    assert result["model_version"] == "synthetic-final-exam-test"
    assert result["prediction_scope"] == "synthetic_demonstration_only"
    assert result["was_clipped_to_valid_range"] is False
