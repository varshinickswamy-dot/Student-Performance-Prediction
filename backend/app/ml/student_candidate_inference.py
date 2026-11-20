"""Opt-in loader and inference for the separate final-exam candidate artifact."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

EXPECTED_FEATURES = [
    "attendance_pct", "study_hours_per_week", "sleep_hours", "previous_sgpa",
    "backlogs", "internal_test_1", "internal_test_2", "assignment_score",
    "extracurricular", "internet_access",
]


class CandidateUnavailableError(RuntimeError):
    pass


@lru_cache(maxsize=2)
def _load_candidate(path_text: str, modified_ns: int):
    path = Path(path_text)
    try:
        artifact = joblib.load(path)
    except Exception as exc:
        raise CandidateUnavailableError("The configured candidate artifact could not be loaded.") from exc
    if artifact.get("promotion_status") != "offline_candidate_only":
        raise CandidateUnavailableError("The configured artifact is not an approved offline candidate.")
    if artifact.get("api_compatible") is not False:
        raise CandidateUnavailableError("The artifact does not match the isolated final-exam API contract.")
    if artifact.get("features") != EXPECTED_FEATURES or artifact.get("target") != "final_exam_score":
        raise CandidateUnavailableError("The candidate feature contract does not match this API.")
    if artifact.get("dataset_provenance") != "synthetic_anonymized_demonstration_dataset":
        raise CandidateUnavailableError("Unexpected dataset provenance for this demonstration endpoint.")
    if not hasattr(artifact.get("pipeline"), "predict"):
        raise CandidateUnavailableError("The candidate artifact does not contain a valid prediction pipeline.")
    return artifact


def get_candidate():
    configured = os.getenv("EDUPREDICT_STUDENT_CANDIDATE_ARTIFACT", "").strip()
    if not configured:
        raise CandidateUnavailableError("The final-exam candidate model is not configured on this server.")
    path = Path(configured).expanduser().resolve()
    if not path.is_file():
        raise CandidateUnavailableError("The configured final-exam candidate artifact was not found.")
    return _load_candidate(str(path), path.stat().st_mtime_ns)


def predict_final_exam_score(inputs: dict) -> dict:
    artifact = get_candidate()
    frame = pd.DataFrame([{name: inputs[name] for name in EXPECTED_FEATURES}], columns=EXPECTED_FEATURES)
    raw_score = float(artifact["pipeline"].predict(frame)[0])
    score = min(100.0, max(0.0, raw_score))
    return {
        "predicted_final_exam_score": round(score, 2),
        "raw_model_output": round(raw_score, 4),
        "was_clipped_to_valid_range": score != raw_score,
        "model_version": artifact["version"],
        "model_type": artifact["model_type"],
        "target": artifact["target"],
        "dataset_provenance": artifact["dataset_provenance"],
        "held_out_test_metrics": artifact.get("metrics", {}),
        "prediction_scope": "synthetic_demonstration_only",
        "disclaimer": (
            "This estimate comes from a generated synthetic demonstration dataset. "
            "It is not validated for real students, is not a grade, and must not be used "
            "for admissions, scholarships, discipline, or other high-impact decisions."
        ),
    }
