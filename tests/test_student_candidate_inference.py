import numpy as np
import pytest

from app.ml import student_candidate_inference as inference


class FakePipeline:
    def __init__(self, value=74.25):
        self.value = value
        self.seen_columns = None

    def predict(self, frame):
        self.seen_columns = list(frame.columns)
        return np.array([self.value])


def sample_inputs():
    return {
        "attendance_pct": 85,
        "study_hours_per_week": 18,
        "sleep_hours": 7,
        "previous_sgpa": 8.2,
        "backlogs": 0,
        "internal_test_1": 38,
        "internal_test_2": 41,
        "assignment_score": 18,
        "extracurricular": True,
        "internet_access": True,
    }


def test_candidate_inference_returns_explicit_synthetic_scope(monkeypatch):
    pipeline = FakePipeline()
    monkeypatch.setattr(inference, "get_candidate", lambda: {
        "pipeline": pipeline,
        "version": "candidate-test-v1",
        "model_type": "ridge",
        "target": "final_exam_score",
        "dataset_provenance": "synthetic_anonymized_demonstration_dataset",
        "metrics": {"mae": 7.5},
    })

    result = inference.predict_final_exam_score(sample_inputs())

    assert result["predicted_final_exam_score"] == 74.25
    assert result["model_version"] == "candidate-test-v1"
    assert result["prediction_scope"] == "synthetic_demonstration_only"
    assert result["held_out_test_metrics"] == {"mae": 7.5}
    assert pipeline.seen_columns == inference.EXPECTED_FEATURES
    assert "not validated for real students" in result["disclaimer"]


def test_candidate_inference_clips_out_of_range_output(monkeypatch):
    monkeypatch.setattr(inference, "get_candidate", lambda: {
        "pipeline": FakePipeline(108.0),
        "version": "candidate-test-v1",
        "model_type": "ridge",
        "target": "final_exam_score",
        "dataset_provenance": "synthetic_anonymized_demonstration_dataset",
        "metrics": {},
    })

    result = inference.predict_final_exam_score(sample_inputs())

    assert result["predicted_final_exam_score"] == 100
    assert result["was_clipped_to_valid_range"] is True
    assert result["raw_model_output"] == 108


def test_candidate_loader_fails_closed_when_artifact_not_configured(monkeypatch):
    inference._load_candidate.cache_clear()
    monkeypatch.delenv("EDUPREDICT_STUDENT_CANDIDATE_ARTIFACT", raising=False)

    with pytest.raises(inference.CandidateUnavailableError, match="not configured"):
        inference.get_candidate()
