"""Offline benchmark for the anonymized synthetic student-performance CSV.

This candidate predicts final_exam_score from information available before the
final exam. It deliberately excludes identifiers, demographics, and outcomes
that would leak the target. It never replaces the deployed Ridge artifact.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    explained_variance_score,
    mean_absolute_error,
    max_error,
    mean_squared_error,
    median_absolute_error,
    r2_score,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "attendance_pct",
    "study_hours_per_week",
    "sleep_hours",
    "previous_sgpa",
    "backlogs",
    "internal_test_1",
    "internal_test_2",
    "assignment_score",
    "extracurricular",
    "internet_access",
]
TARGET = "final_exam_score"
GROUP = "student_id"
BOOLEAN_FEATURES = {"extracurricular", "internet_access"}
NUMERIC_BOUNDS = {
    "attendance_pct": (0, 100),
    "study_hours_per_week": (0, 60),
    "sleep_hours": (0, 24),
    "previous_sgpa": (0, 10),
    "backlogs": (0, 30),
    "internal_test_1": (0, 50),
    "internal_test_2": (0, 50),
    "assignment_score": (0, 20),
}
BOOLEAN_VALUES = {
    "yes": 1, "no": 0, "true": 1, "false": 0,
    "1": 1, "0": 0, "y": 1, "n": 0,
}
EXCLUDED_COLUMNS = [
    "student_id (grouping only; never a model feature)",
    "overall_score (contains/depends on final assessment outcome)",
    "grade (derived outcome)",
    "result (derived outcome)",
    "gender, age, branch, residence_area, semester, part_time_job (not used as model inputs)",
]


def _metrics(actual: pd.Series, predicted: np.ndarray) -> dict:
    return {
        "mae": round(float(mean_absolute_error(actual, predicted)), 4),
        "rmse": round(float(mean_squared_error(actual, predicted) ** 0.5), 4),
        "median_absolute_error": round(float(median_absolute_error(actual, predicted)), 4),
        "r2": round(float(r2_score(actual, predicted)), 4),
        "explained_variance": round(float(explained_variance_score(actual, predicted)), 4),
        "max_absolute_error": round(float(max_error(actual, predicted)), 4),
    }


def prepare_student_dataset(frame: pd.DataFrame):
    required = [GROUP, *FEATURES, TARGET]
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing_columns)}")

    source_rows = len(frame)
    data = frame[required].copy()
    missing_by_column = {name: int(count) for name, count in data.isna().sum().items()}
    data[GROUP] = data[GROUP].astype("string").str.strip()
    data.loc[data[GROUP] == "", GROUP] = pd.NA

    invalid_boolean_values = {}
    for name in BOOLEAN_FEATURES:
        normalized = data[name].astype("string").str.strip().str.casefold()
        mapped = normalized.map(BOOLEAN_VALUES)
        invalid = data[name].notna() & mapped.isna()
        if invalid.any():
            invalid_boolean_values[name] = int(invalid.sum())
        data[name] = mapped

    numeric_features = [name for name in FEATURES if name not in BOOLEAN_FEATURES]
    for name in [*numeric_features, TARGET]:
        data[name] = pd.to_numeric(data[name], errors="coerce")
    if invalid_boolean_values:
        raise ValueError(f"Boolean columns contain unsupported values: {invalid_boolean_values}")

    duplicate_rows = int(data.duplicated().sum())
    data = data.drop_duplicates()
    incomplete_rows = int(data.isna().any(axis=1).sum())
    data = data.dropna()
    if len(data) < 100:
        raise ValueError(f"At least 100 complete unique rows are required; found {len(data)}.")
    if data[GROUP].nunique() < 7:
        raise ValueError("At least seven unique anonymized student IDs are required for grouped evaluation.")
    if not data[TARGET].between(0, 100).all():
        raise ValueError("final_exam_score must be between 0 and 100.")
    for name, (minimum, maximum) in NUMERIC_BOUNDS.items():
        if not data[name].between(minimum, maximum).all():
            raise ValueError(f"{name} contains values outside the supported range {minimum}–{maximum}.")
    if not data[list(BOOLEAN_FEATURES)].isin([0, 1]).all().all():
        raise ValueError("Boolean features must use Yes/No, True/False, or 1/0.")

    X = data[FEATURES].astype(float)
    y = data[TARGET].astype(float)
    groups = data[GROUP].astype(str)

    feature_summary = {
        name: {
            "minimum": round(float(X[name].min()), 4),
            "maximum": round(float(X[name].max()), 4),
            "mean": round(float(X[name].mean()), 4),
            "unique_values": int(X[name].nunique()),
        }
        for name in FEATURES
    }
    iqr_outliers = {}
    for name in FEATURES:
        q1, q3 = X[name].quantile([0.25, 0.75])
        spread = q3 - q1
        lower, upper = q1 - 1.5 * spread, q3 + 1.5 * spread
        iqr_outliers[name] = int(((X[name] < lower) | (X[name] > upper)).sum())

    quality = {
        "provenance": "synthetic_anonymized_demonstration_dataset",
        "source_rows": int(source_rows),
        "valid_rows": int(len(data)),
        "duplicate_rows_removed": duplicate_rows,
        "incomplete_rows_removed": incomplete_rows,
        "missing_values_by_column_before_cleaning": missing_by_column,
        "unique_student_groups": int(groups.nunique()),
        "repeated_student_groups": int((groups.value_counts() > 1).sum()),
        "feature_columns": FEATURES,
        "excluded_columns": EXCLUDED_COLUMNS,
        "feature_summary": feature_summary,
        "iqr_outlier_counts_review_only": iqr_outliers,
        "target_summary": {
            "minimum": round(float(y.min()), 4),
            "maximum": round(float(y.max()), 4),
            "mean": round(float(y.mean()), 4),
            "standard_deviation": round(float(y.std(ddof=0)), 4),
            "median": round(float(y.median()), 4),
        },
        "target_feature_correlations": {
            name: round(float(X[name].corr(y)), 4) for name in FEATURES
        },
        "interpretation": (
            "Synthetic-data diagnostics only. Correlation and IQR flags are screening signals, "
            "not proof of leakage, causation, or real-world representativeness."
        ),
    }
    return X, y, groups, quality


def train_student_candidate(frame: pd.DataFrame, fingerprint: str = "in-memory-synthetic"):
    X, y, groups, quality = prepare_student_dataset(frame)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    groups_train, groups_test = groups.iloc[train_idx], groups.iloc[test_idx]
    if not set(groups_train).isdisjoint(set(groups_test)):
        raise RuntimeError("Student-group leakage detected between train and test.")
    if groups_train.nunique() < 5:
        raise ValueError("The training partition must contain at least five student groups.")

    cv = GroupKFold(n_splits=5)
    candidates = {
        "ridge": Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))]),
        "random_forest": RandomForestRegressor(
            n_estimators=250, min_samples_leaf=2, random_state=42, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=150, learning_rate=0.05, max_depth=2, random_state=42
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=150, learning_rate=0.08, l2_regularization=1.0, random_state=42
        ),
    }
    comparisons = []
    for name, estimator in candidates.items():
        scores = cross_val_score(
            estimator, X_train, y_train, cv=cv, groups=groups_train,
            scoring="neg_mean_absolute_error", n_jobs=1,
        )
        comparisons.append({
            "model": name,
            "cross_validation_mae_mean": round(float(-scores.mean()), 4),
            "cross_validation_mae_std": round(float(scores.std()), 4),
            "folds": int(len(scores)),
        })
    comparisons.sort(key=lambda item: item["cross_validation_mae_mean"])
    selected_name = comparisons[0]["model"]
    selected = candidates[selected_name]
    selected.fit(X_train, y_train)
    predictions = selected.predict(X_test)

    baseline = DummyRegressor(strategy="mean").fit(X_train, y_train)
    baseline_predictions = baseline.predict(X_test)
    selected_metrics = _metrics(y_test, predictions)
    baseline_metrics = _metrics(y_test, baseline_predictions)
    baseline_mae = baseline_metrics["mae"]
    improvement = (
        round((baseline_mae - selected_metrics["mae"]) / baseline_mae * 100, 2)
        if baseline_mae else None
    )
    residuals = predictions - y_test.to_numpy()
    version = f"synthetic-final-exam-{selected_name}-{fingerprint[:10]}"
    created_at = datetime.now(timezone.utc).isoformat()

    artifact = {
        "pipeline": selected,
        "features": FEATURES,
        "target": TARGET,
        "version": version,
        "model_type": selected_name,
        "dataset_provenance": "synthetic_anonymized_demonstration_dataset",
        "dataset_fingerprint": fingerprint,
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "metrics": selected_metrics,
        "baseline_metrics": baseline_metrics,
        "created_at": created_at,
        "scikit_learn_version": sklearn.__version__,
        "api_compatible": False,
        "promotion_status": "offline_candidate_only",
        "compatibility_note": (
            "This candidate uses a separate final_exam_score feature contract. "
            "It does not replace or alter the deployed /api/predictions/predict Ridge model."
        ),
    }
    report = {
        "report_version": "1.0",
        "created_at": created_at,
        "candidate_version": version,
        "dataset_provenance": quality["provenance"],
        "dataset_fingerprint": fingerprint,
        "quality": quality,
        "split": {
            "strategy": "GroupShuffleSplit 80/20 by anonymized student_id; GroupKFold 5-fold CV",
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "train_student_groups": int(groups_train.nunique()),
            "test_student_groups": int(groups_test.nunique()),
            "groups_disjoint": set(groups_train).isdisjoint(set(groups_test)),
            "random_seed": 42,
        },
        "selection_method": "Lowest mean 5-fold training-only grouped CV MAE",
        "selected_model": selected_name,
        "candidate_comparison": comparisons,
        "held_out_test_metrics": selected_metrics,
        "mean_baseline_test_metrics": baseline_metrics,
        "mae_improvement_over_mean_baseline_percent": improvement,
        "residual_summary": {
            "mean_error_prediction_minus_actual": round(float(np.mean(residuals)), 4),
            "p90_absolute_error": round(float(np.quantile(np.abs(residuals), 0.9)), 4),
            "maximum_absolute_error": round(float(np.max(np.abs(residuals))), 4),
        },
        "limitations": [
            "All records are synthetic and anonymized; these metrics do not establish real-world performance.",
            "student_id is used only to isolate groups and is never a model feature.",
            "overall_score, grade, result, demographics, and identifiers are excluded from model inputs.",
            "The target is final_exam_score, predicted from pre-final academic and study inputs.",
            "This candidate is not compatible with the current deployed prediction API and is not promoted.",
            "No causal, calibrated-probability, admission, grading, or high-stakes interpretation is supported.",
        ],
        "software": {
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    return artifact, report


def main() -> None:
    dataset_path = os.getenv("EDUPREDICT_STUDENT_DATASET_PATH")
    if not dataset_path:
        raise SystemExit(
            "Set EDUPREDICT_STUDENT_DATASET_PATH to the synthetic anonymized CSV. "
            "This command never uses a fallback dataset."
        )
    path = Path(dataset_path).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"Dataset file not found: {path}")
    raw = path.read_bytes()
    fingerprint = hashlib.sha256(raw).hexdigest()
    frame = pd.read_csv(path)
    artifact, report = train_student_candidate(frame, fingerprint)
    output_dir = Path(os.getenv(
        "EDUPREDICT_STUDENT_CANDIDATE_DIR",
        Path(__file__).resolve().parent / "model_artifacts" / "candidates",
    ))
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"{artifact['version']}.joblib"
    report_path = output_dir / f"{artifact['version']}.json"
    joblib.dump(artifact, artifact_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "candidate_artifact": str(artifact_path),
        "evaluation_report": str(report_path),
        "selected_model": report["selected_model"],
        "held_out_test_metrics": report["held_out_test_metrics"],
        "mean_baseline_test_metrics": report["mean_baseline_test_metrics"],
        "api_compatible": artifact["api_compatible"],
        "production_model_replaced": False,
    }, indent=2))


if __name__ == "__main__":
    main()
