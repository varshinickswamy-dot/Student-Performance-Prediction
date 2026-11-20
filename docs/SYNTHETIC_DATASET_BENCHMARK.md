# Synthetic Student Dataset Benchmark

## Dataset handling

A 1,000-row generated and anonymized demonstration CSV was supplied for this project. It is not real institutional data and must not be described as evidence of real-world student outcomes. The raw file is intentionally not committed by this workflow; keep local copies in a controlled project data folder and do not upload real student records to the public repository.

## Candidate task

The offline candidate predicts final_exam_score from fields available before the final exam:

- attendance_pct
- study_hours_per_week
- sleep_hours
- previous_sgpa
- backlogs
- internal_test_1
- internal_test_2
- assignment_score
- extracurricular
- internet_access

student_id is used only for grouped splitting and never becomes a model feature. overall_score, grade, and result are excluded because they are derived from academic outcomes and can leak the target. Demographic and contextual fields such as gender, age, branch, residence area, semester, and part-time-job status are not used as model inputs.

The task is deliberately a final-exam score estimate from pre-final information. It is not a pass/fail classifier and does not output calibrated probabilities.

## Reproduce locally

From the repository root in PowerShell:

    cd backend
    $env:EDUPREDICT_STUDENT_DATASET_PATH="D:\path\to\student_performance.csv"
    python -m app.ml.train_student_candidate

The script validates the schema and ranges, audits missingness, duplicate rows, outliers for review, and target correlations, then compares Ridge, Random Forest, Gradient Boosting, and Histogram Gradient Boosting. It uses an 80/20 GroupShuffleSplit by anonymized student ID, selects using five-fold GroupKFold MAE on training data, and evaluates the selected model once on the held-out set against a mean baseline.

The script writes a Joblib candidate and JSON evaluation report under backend/app/ml/model_artifacts/candidates/. These outputs are local artifacts and should not be committed unless reviewed and intentionally published.

## Compatibility and production safety

This is a separate candidate feature contract. It is NOT compatible with the existing deployed /api/predictions/predict contract and is not wired into Render startup. It does not replace ridge_model.joblib, alter model versioning, migrate the database, or change the current Vercel/Render integration.

The deployed Ridge model remains the production model until a separate compatibility, provenance, fairness, subgroup-error, and shadow-evaluation review approves a versioned migration. Because this benchmark uses generated synthetic data, its metrics are a software demonstration only. Do not use the candidate for grading, admissions, scholarships, discipline, or other high-impact decisions.
