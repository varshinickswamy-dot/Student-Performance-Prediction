# Final-exam candidate API (opt-in)

## Endpoint

Authenticated students may call `POST /api/student/final-exam-prediction` with these pre-final inputs:

- `attendance_pct`: 0–100
- `study_hours_per_week`: 0–60
- `sleep_hours`: 0–24
- `previous_sgpa`: 0–10
- `backlogs`: 0–30
- `internal_test_1` and `internal_test_2`: 0–50 each
- `assignment_score`: 0–20
- `extracurricular` and `internet_access`: booleans

The endpoint returns a separately labeled synthetic demonstration estimate, candidate version, model type, and held-out evaluation metadata. It does not write to the existing prediction history and does not call or replace the deployed Ridge model.

## Configure only after reviewing the artifact

Set `EDUPREDICT_STUDENT_CANDIDATE_ARTIFACT` on the backend to the absolute path of a reviewed candidate artifact. The file must be built with the same Python/scikit-learn dependency versions as the deployed service. Do not use a Joblib artifact across unverified scikit-learn versions.

If the environment variable is missing, the file is absent, or its feature contract/provenance does not match, the endpoint returns HTTP 503 and leaves the existing API operational. No candidate artifact is committed to Git.

The candidate is trained on generated synthetic data. Its metrics are only a reproducible software demonstration and must not be represented as real-world academic accuracy or used for grading, admissions, scholarships, discipline, or other high-impact decisions.
