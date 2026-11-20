import numpy as np
import pandas as pd
import pytest

from app.ml.train_student_candidate import (
    FEATURES,
    TARGET,
    prepare_student_dataset,
    train_student_candidate,
)


def synthetic_student_frame(rows=180):
    rng = np.random.default_rng(42)
    attendance = rng.uniform(45, 100, rows)
    study = rng.uniform(1, 28, rows)
    previous = rng.uniform(4, 10, rows)
    test_one = rng.uniform(10, 50, rows)
    test_two = rng.uniform(10, 50, rows)
    assignment = rng.uniform(3, 20, rows)
    score = (
        0.22 * attendance + 0.65 * study + 2.2 * previous
        + 0.42 * test_one + 0.38 * test_two + 0.55 * assignment
        + rng.normal(0, 7, rows)
    ).clip(0, 100)
    return pd.DataFrame({
        "student_id": [f"SYN{i:05d}" for i in range(rows)],
        "attendance_pct": attendance,
        "study_hours_per_week": study,
        "sleep_hours": rng.uniform(4, 9, rows),
        "previous_sgpa": previous,
        "backlogs": rng.integers(0, 4, rows),
        "internal_test_1": test_one,
        "internal_test_2": test_two,
        "assignment_score": assignment,
        "extracurricular": rng.choice(["Yes", "No"], rows),
        "internet_access": rng.choice(["Yes", "No"], rows),
        "final_exam_score": score,
        "overall_score": score * 0.8,
        "grade": rng.choice(list("ABCDF"), rows),
        "result": rng.choice(["Pass", "Fail"], rows),
        "gender": rng.choice(["Female", "Male", "Other"], rows),
    })


def test_student_candidate_excludes_identifiers_demographics_and_derived_outcomes():
    frame = synthetic_student_frame()
    X, y, groups, quality = prepare_student_dataset(frame)
    assert list(X.columns) == FEATURES
    assert TARGET == "final_exam_score"
    assert "student_id" not in X.columns
    assert "overall_score" not in X.columns
    assert "grade" not in X.columns
    assert "result" not in X.columns
    assert "gender" not in X.columns
    assert len(X) == len(y) == len(groups) == 180
    assert quality["provenance"] == "synthetic_anonymized_demonstration_dataset"


def test_student_candidate_uses_group_isolated_holdout_and_does_not_promote():
    frame = synthetic_student_frame(240)
    artifact, report = train_student_candidate(frame, "unit-test-fingerprint")
    assert artifact["api_compatible"] is False
    assert artifact["promotion_status"] == "offline_candidate_only"
    assert artifact["training_rows"] + artifact["test_rows"] == 240
    assert report["split"]["groups_disjoint"] is True
    assert report["split"]["train_student_groups"] + report["split"]["test_student_groups"] == 240
    assert report["selected_model"] in {
        "ridge", "random_forest", "gradient_boosting", "hist_gradient_boosting"
    }
    assert len(report["candidate_comparison"]) == 4
    assert report["held_out_test_metrics"]["mae"] >= 0
    assert report["mean_baseline_test_metrics"]["mae"] >= 0
    assert report["quality"]["excluded_columns"]


def test_student_candidate_rejects_invalid_boolean_values():
    frame = synthetic_student_frame()
    frame["internet_access"] = frame["internet_access"].astype(object)
    frame.loc[0, "internet_access"] = "sometimes"
    with pytest.raises(ValueError, match="unsupported values"):
        prepare_student_dataset(frame)


def test_student_candidate_rejects_missing_required_columns_and_invalid_target():
    frame = synthetic_student_frame()
    with pytest.raises(ValueError, match="missing required columns"):
        prepare_student_dataset(frame.drop(columns=["attendance_pct"]))
    frame.loc[0, "final_exam_score"] = 101
    with pytest.raises(ValueError, match="between 0 and 100"):
        prepare_student_dataset(frame)
