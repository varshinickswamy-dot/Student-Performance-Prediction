"""Leakage-aware offline candidate training; never replaces the live production artifact."""
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
from sklearn.model_selection import (
    GroupKFold,
    GroupShuffleSplit,
    KFold,
    cross_val_score,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.predictor import FEATURES

BOOLEAN_FEATURES = {"extracurricular", "internet_access", "family_support"}
NUMERIC_BOUNDS = {
    "study_hours": (0, 16),
    "previous_marks": (0, 100),
    "attendance": (0, 100),
    "assignment_scores": (0, 100),
    "class_participation": (0, 100),
    "homework_completion": (0, 100),
    "sleep_hours": (0, 16),
}
BOOLEAN_VALUES = {
    "true": 1, "false": 0, "yes": 1, "no": 0,
    "1": 1, "0": 0, "y": 1, "n": 0,
}


def _correlation_audit(data: pd.DataFrame, target_column: str) -> dict:
    """Flag unusually strong correlations for human leakage review, not as proof."""
    feature_corr = data[FEATURES].corr().abs()
    high_pairs = []
    for i, left in enumerate(FEATURES):
        for right in FEATURES[i + 1:]:
            value = feature_corr.loc[left, right]
            if pd.notna(value) and float(value) >= 0.98:
                high_pairs.append({
                    "feature_a": left, "feature_b": right,
                    "absolute_correlation": round(float(value), 4),
                })
    target_corr = data[FEATURES].corrwith(data[target_column]).abs()
    high_target = [
        {"feature": name, "absolute_correlation": round(float(value), 4)}
        for name, value in target_corr.items()
        if pd.notna(value) and float(value) >= 0.98
    ]
    warnings = []
    if high_pairs:
        warnings.append("Highly correlated feature pairs require duplicate-signal and leakage review.")
    if high_target:
        warnings.append("Features almost perfectly correlated with the target require leakage and target-definition review.")
    return {
        "highly_correlated_feature_pairs": high_pairs,
        "near_perfect_feature_target_correlations": high_target,
        "correlation_warning_threshold": 0.98,
        "warnings": warnings,
        "interpretation": "Correlation flags are screening signals only; they do not establish leakage or causality.",
    }


def _prepare_dataset(
    frame: pd.DataFrame,
    target_column: str,
    group_column: str | None = None,
) -> tuple[pd.DataFrame, pd.Series, dict, pd.Series | None]:
    if target_column in FEATURES:
        raise ValueError("The target column cannot also be one of the model input features.")
    if group_column and (group_column in FEATURES or group_column == target_column):
        raise ValueError("The grouping column must be separate from model features and target.")
    required = [*FEATURES, target_column] + ([group_column] if group_column else [])
    missing_columns = [name for name in required if name not in frame.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing_columns)}")
    if len(set(required)) != len(required):
        raise ValueError("Dataset feature, target, and grouping column names must be distinct.")

    source_rows = len(frame)
    data = frame[required].copy()
    missing_by_column = {
        name: int(count) for name, count in data.isna().sum().items()
    }

    invalid_boolean_values = {}
    for name in BOOLEAN_FEATURES:
        original = data[name]
        if original.dtype == object:
            normalized = original.astype("string").str.strip().str.casefold()
            mapped = normalized.map(BOOLEAN_VALUES)
            invalid = original.notna() & mapped.isna()
            if invalid.any():
                invalid_boolean_values[name] = int(invalid.sum())
            data[name] = mapped
        data[name] = pd.to_numeric(data[name], errors="coerce")
    if invalid_boolean_values:
        details = ", ".join(f"{name}: {count}" for name, count in invalid_boolean_values.items())
        raise ValueError(f"Boolean columns contain unsupported values ({details}); use true/false, yes/no, or 1/0.")

    numeric_features = [name for name in FEATURES if name not in BOOLEAN_FEATURES]
    for name in [*numeric_features, target_column]:
        data[name] = pd.to_numeric(data[name], errors="coerce")

    duplicates = int(data.duplicated().sum())
    data = data.drop_duplicates()
    incomplete_rows = int(data.isna().any(axis=1).sum())
    data = data.dropna()
    if len(data) < 100:
        raise ValueError(f"At least 100 complete, unique rows are required; found {len(data)}.")
    if group_column and data[group_column].nunique() < 7:
        raise ValueError(
            "At least seven unique groups are required so a 20% group holdout can leave "
            "five groups for GroupKFold cross-validation."
        )
    if not data[target_column].between(0, 100).all():
        raise ValueError("The regression target must contain values between 0 and 100.")
    if not data[list(BOOLEAN_FEATURES)].isin([0, 1]).all().all():
        raise ValueError("Boolean feature columns must contain true/false, yes/no, or 1/0 values.")
    for name, (minimum, maximum) in NUMERIC_BOUNDS.items():
        if not data[name].between(minimum, maximum).all():
            raise ValueError(f"{name} contains values outside the supported range {minimum}–{maximum}.")

    quality_frame = data[[*FEATURES, target_column]].copy()
    groups = data[group_column].copy() if group_column else None
    target = data[target_column].astype(float)
    feature_summary = {
        name: {
            "minimum": round(float(quality_frame[name].min()), 4),
            "maximum": round(float(quality_frame[name].max()), 4),
            "mean": round(float(quality_frame[name].mean()), 4),
            "standard_deviation": round(float(quality_frame[name].std(ddof=0)), 4),
            "unique_values": int(quality_frame[name].nunique()),
        }
        for name in FEATURES
    }
    target_summary = {
        "minimum": round(float(target.min()), 4),
        "maximum": round(float(target.max()), 4),
        "mean": round(float(target.mean()), 4),
        "standard_deviation": round(float(target.std(ddof=0)), 4),
        "median": round(float(target.median()), 4),
        "p05": round(float(target.quantile(0.05)), 4),
        "p25": round(float(target.quantile(0.25)), 4),
        "p75": round(float(target.quantile(0.75)), 4),
        "p95": round(float(target.quantile(0.95)), 4),
        "unique_values": int(target.nunique()),
    }
    correlation_audit = _correlation_audit(quality_frame, target_column)
    quality = {
        "source_rows": int(source_rows),
        "valid_rows": int(len(data)),
        "duplicate_rows_removed": duplicates,
        "incomplete_rows_removed": incomplete_rows,
        "missing_values_by_column_before_cleaning": missing_by_column,
        "invalid_boolean_values": invalid_boolean_values,
        "target_column": target_column,
        "feature_columns": FEATURES,
        "group_column_used": group_column,
        "unique_groups": int(groups.nunique()) if groups is not None else None,
        "constant_features": [
            name for name in FEATURES if quality_frame[name].nunique() <= 1
        ],
        "feature_summary": feature_summary,
        "target_summary": target_summary,
        "correlation_audit": correlation_audit,
    }
    return data[FEATURES].astype(float), target, quality, groups


def _regression_metrics(actual: pd.Series, predicted: np.ndarray) -> dict:
    return {
        "mae": round(float(mean_absolute_error(actual, predicted)), 4),
        "rmse": round(float(mean_squared_error(actual, predicted) ** 0.5), 4),
        "median_absolute_error": round(float(median_absolute_error(actual, predicted)), 4),
        "r2": round(float(r2_score(actual, predicted)), 4),
        "explained_variance": round(float(explained_variance_score(actual, predicted)), 4),
        "max_absolute_error": round(float(max_error(actual, predicted)), 4),
    }


def train_candidate_from_frame(
    frame: pd.DataFrame,
    target_column: str = "score",
    source_fingerprint: str = "in-memory-dataset",
    group_column: str | None = None,
) -> tuple[dict, dict]:
    X, y, quality, groups = _prepare_dataset(frame, target_column, group_column)
    if groups is not None:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_indices, test_indices = next(splitter.split(X, y, groups))
        X_train, X_test = X.iloc[train_indices], X.iloc[test_indices]
        y_train, y_test = y.iloc[train_indices], y.iloc[test_indices]
        groups_train, groups_test = groups.iloc[train_indices], groups.iloc[test_indices]
        if groups_train.nunique() < 5:
            raise ValueError("The grouped holdout left fewer than five training groups; provide more unique groups.")
        groups_disjoint = set(groups_train) .isdisjoint(set(groups_test))
        if not groups_disjoint:
            raise RuntimeError("Group leakage detected between training and held-out test partitions.")
        folds = GroupKFold(n_splits=5)
        split_strategy = "GroupShuffleSplit + GroupKFold; student/group entities isolated across train/test and CV folds"
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        groups_train = None
        groups_disjoint = None
        folds = KFold(n_splits=5, shuffle=True, random_state=42)
        split_strategy = "Random 80/20 holdout + shuffled 5-fold CV; use a group column for repeated student records"

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

    comparison = []
    fitted = {}
    for name, estimator in candidates.items():
        scores = cross_val_score(
            estimator, X_train, y_train, cv=folds, groups=groups_train,
            scoring="neg_mean_absolute_error", n_jobs=1,
        )
        fitted[name] = estimator
        comparison.append({
            "model": name,
            "cross_validation_mae_mean": round(float(-scores.mean()), 4),
            "cross_validation_mae_std": round(float(scores.std()), 4),
            "cross_validation_fold_count": int(len(scores)),
        })

    comparison.sort(key=lambda item: item["cross_validation_mae_mean"])
    selected_name = comparison[0]["model"]
    selected = fitted[selected_name]
    selected.fit(X_train, y_train)
    test_predictions = selected.predict(X_test)
    metrics = _regression_metrics(y_test, test_predictions)

    baseline = DummyRegressor(strategy="mean")
    baseline.fit(X_train, y_train)
    baseline_predictions = baseline.predict(X_test)
    baseline_metrics = _regression_metrics(y_test, baseline_predictions)
    baseline_mae = baseline_metrics["mae"]
    mae_improvement_percent = (
        round((baseline_mae - metrics["mae"]) / baseline_mae * 100, 2)
        if baseline_mae > 0 else None
    )
    absolute_errors = np.abs(y_test.to_numpy() - test_predictions)
    residuals = test_predictions - y_test.to_numpy()

    version = f"candidate-{selected_name}-{source_fingerprint[:10]}"
    created_at = datetime.now(timezone.utc).isoformat()
    artifact = {
        "pipeline": selected,
        "features": FEATURES,
        "feature_schema_version": "1.0",
        "version": version,
        "model_type": selected_name,
        "target_column": target_column,
        "dataset_fingerprint": source_fingerprint,
        "dataset": "User-supplied candidate dataset; provenance must be verified",
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "metrics": metrics,
        "baseline_metrics": baseline_metrics,
        "created_at": created_at,
        "scikit_learn_version": sklearn.__version__,
    }
    report = {
        "report_version": "1.0",
        "created_at": created_at,
        "version": version,
        "selected_model": selected_name,
        "dataset_fingerprint": source_fingerprint,
        "quality": quality,
        "split": {
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "test_fraction": 0.2,
            "strategy": split_strategy,
            "group_count_train": int(groups_train.nunique()) if groups_train is not None else None,
            "group_count_test": int(groups.iloc[test_indices].nunique()) if groups is not None else None,
            "groups_disjoint": groups_disjoint,
            "random_seed": 42,
        },
        "selection_method": "Lowest mean 5-fold cross-validation MAE on training split only",
        "held_out_test_metrics": metrics,
        "mean_baseline_test_metrics": baseline_metrics,
        "mae_improvement_over_mean_baseline_percent": mae_improvement_percent,
        "residual_summary": {
            "mean_error_prediction_minus_actual": round(float(np.mean(residuals)), 4),
            "standard_deviation": round(float(np.std(residuals)), 4),
            "median_absolute_error": round(float(np.median(absolute_errors)), 4),
            "p90_absolute_error": round(float(np.quantile(absolute_errors, 0.90)), 4),
            "maximum_absolute_error": round(float(np.max(absolute_errors)), 4),
        },
        "candidate_comparison": comparison,
        "software": {"scikit_learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
        "limitations": [
            "This is a candidate artifact and does not replace the live production artifact.",
            "Verify dataset provenance, consent/legal basis, target meaning, and representativeness before use.",
            "Held-out metrics describe this dataset and split only; they do not guarantee future or institutional performance.",
            "Correlation flags are screening signals, not proof of leakage; review flagged features with subject-matter experts.",
            "Review subgroup errors, temporal generalization, and feature availability at prediction time before production promotion.",
            "This is a regression task; classification probabilities and calibration metrics are not applicable to this score output.",
        ],
    }
    return artifact, report


def main() -> None:
    dataset_path = os.getenv("EDUPREDICT_DATASET_PATH")
    if not dataset_path:
        raise SystemExit(
            "Set EDUPREDICT_DATASET_PATH to an authorized CSV dataset. "
            "No synthetic fallback is used by this candidate-training command."
        )
    path = Path(dataset_path).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"Dataset file not found: {path}")
    raw_bytes = path.read_bytes()
    fingerprint = hashlib.sha256(raw_bytes).hexdigest()
    frame = pd.read_csv(path)
    target = os.getenv("EDUPREDICT_TARGET_COLUMN", "score")
    group_column = os.getenv("EDUPREDICT_GROUP_COLUMN") or None
    artifact, report = train_candidate_from_frame(frame, target, fingerprint, group_column)

    artifact_dir = Path(os.getenv(
        "EDUPREDICT_CANDIDATE_DIR",
        Path(__file__).resolve().parent / "model_artifacts" / "candidates",
    ))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{artifact['version']}.joblib"
    report_path = artifact_dir / f"{artifact['version']}.json"
    joblib.dump(artifact, artifact_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "candidate_artifact": str(artifact_path),
        "evaluation_report": str(report_path),
        "selected_model": report["selected_model"],
        "held_out_test_metrics": report["held_out_test_metrics"],
        "mean_baseline_test_metrics": report["mean_baseline_test_metrics"],
        "live_model_replaced": False,
    }, indent=2))


if __(!)__name__ == "__main__":
    main()
