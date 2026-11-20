# Demonstration Dataset

The repository started without an existing dataset. The application therefore includes a
seeded, synthetic demonstration dataset for development and evaluation. It is not a
real student record and must not be used for high-stakes decisions.

Training features:
- study_hours
- previous_marks
- attendance
- assignment_scores
- class_participation
- homework_completion
- sleep_hours
- extracurricular
- internet_access
- family_support

The regression target is `predicted_score`, a 0–100 academic score.


## Preparing an authorized real dataset

No real student dataset is currently included in this repository. Before training, obtain data with documented provenance and permission, remove direct identifiers, and verify that each target is an observed outcome with a consistent meaning.

The offline candidate trainer expects the feature columns above and a numeric target column in the range 0–100. The default target name is `score`; set `EDUPREDICT_TARGET_COLUMN` if the source uses another column name. Boolean features accept true/false, yes/no, or 1/0. All numeric features must follow the supported ranges documented in `docs/ML_METHODOLOGY.md`.

For repeated records per student, set `EDUPREDICT_GROUP_COLUMN` to a stable grouping column such as an anonymized student key. The grouping column is used only for leakage-aware train/test and cross-validation splits; it is not included as a model input. Never include names, email addresses, student IDs or other direct identifiers as model features.

Run the candidate trainer from the backend directory:

```powershell
$env:EDUPREDICT_DATASET_PATH="D:\\secure-data\\authorized_academic_data.csv"
$env:EDUPREDICT_TARGET_COLUMN="score"
# Optional for longitudinal records:
$env:EDUPREDICT_GROUP_COLUMN="student_group"
python -m app.ml.train_candidate
```

The output is a candidate artifact and evaluation report under `backend/app/ml/model_artifacts/candidates/`. It does not replace the live deployed model. Do not commit private data, private reports, or model artifacts derived from confidential records.
