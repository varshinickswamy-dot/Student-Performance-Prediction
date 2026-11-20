"""Offline candidate-model training. This never replaces the live production artifact."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.predictor import FEATURES

BOOLEAN_FEATURES = {"extracurricular", "internet_access", "family_support"}


def _prepare_dataset(frame: pd.DataFrame, target_column: str, group_column: str | None = None) -> tuple[pd.DataFrame, pd.Series, dict, pd.Series | None]:
    required = [*FEATURES, target_column] + ([group_column] if group_column else [])
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")

    source_rows = len(frame)
    data = frame[required].copy()
    duplicates = int(data.duplicated().sum())
    data = data.drop_duplicates()

    for name in BOOLEAN_FEATURES:
        if data[name].dtype == object:
            normalized = data[name].astype(str).str.strip().str.casefold()
            data[name] = normalized.map({
                "true": 1, "false": 0, "yes": 1, "no": 0,
                "1": 1, "0": 0, "y": 1, "n": 0,
            })
        data[name] = pd.to_numeric(data[name], errors="coerce")

    numeric_features = [name for name in FEATURES if name not in BOOLEAN_FEATURES]
    for name in [*numeric_features, target_column]:
        data[name] = pd.to_numeric(data[name], errors="coerce")

    missing_rows = int(data.isna().any(axis=1).sum())
    data = data.dropna()
    if len(data) < 100:
        raise ValueError(
            f"At least 100 complete, unique rows are required; found {len(data)}."
        )
    if not data[target_column].between(0, 100).all():
        raise ValueError("The regression target must contain values between 0 and 100.")
    if not data[list(BOOLEAN_FEATURES)].isin([0, 1]).all().all():
        raise ValueError("Boolean feature columns must contain true/false, yes/no, or 1/0 values.")

    bounds = {
        "study_hours": (0, 16), "previous_marks": (0, 100),
        "attendance": (0, 100), "assignment_scores": (0, 100),
        "class_participation": (0, 100), "homework_completion": (0, 100),
        "sleep_hours": (0, 16),
    }
    for name, (minimum, maximum) in bounds.items():
        if not data[name].between(minimum, maximum).all():
            raise ValueError(f"{name} contains values outside the supported range {minimum}–{maximum}.")

    groups = data[group_column].copy() if group_column else None
    quality = {
        "source_rows": source_rows,
        "valid_rows": int(len(data)),
        "duplicate_rows_removed": duplicates,
        "incomplete_rows_removed": missing_rows,
        "target_column": target_column,
        "feature_columns": FEATURES,
        "group_column_used": group_column,
        "unique_groups": int(groups.nunique()) if groups is not None else None,
    }
    return data[FEATURES].astype(float), data[target_column].astype(float), quality, groups


def train_candidate_from_frame(
    frame: pd.DataFrame,
    target_column: str = "score",
    source_fingerprint: str = "in-memory-dataset",
    group_column: str | None = None,
) -> tuple[dict, dict]:
    X, y, quality, groups = _prepare_dataset(frame, target_column, group_column)
    if groups is not None:
        if groups.nunique() < 5:
            raise ValueError("At least five unique groups are required for group-aware cross-validation.")
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_indices, test_indices = next(splitter.split(X, y, groups))
        X_train, X_test = X.iloc[train_indices], X.iloc[test_indices]
        y_train, y_test = y.iloc[train_indices], y.iloc[test_indices]
        groups_train = groups.iloc[train_indices]
        folds = GroupKFold(n_splits=5)
        split_strategy = "GroupShuffleSplit + GroupKFold; groups isolated across train/test and folds"
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        groups_train = None
        folds = KFold(n_splits=5, shuffle=True, random_state=42)
        split_strategy = "Random 80/20 holdout + shuffled 5-fold CV"
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
        })

    comparison.sort(key=lambda item: item["cross_validation_mae_mean"])
    selected_name = comparison[0]["model"]
    selected = fitted[selected_name]
    selected.fit(X_train, y_train)
    test_predictions = selected.predict(X_test)
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, test_predictions)), 4),
        "rmse": round(float(mean_squared_error(y_test, test_predictions) ** 0.5), 4),
        "r2": round(float(r2_score(y_test, test_predictions)), 4),
    }
    version = f"candidate-{selected_name}-{source_fingerprint[:10]}"
    artifact = {
        "pipeline": selected,
        "features": FEATURES,
        "version": version,
        "model_type": selected_name,
        "target_column": target_column,
        "dataset_fingerprint": source_fingerprint,
        "dataset": "User-supplied candidate dataset; provenance must be verified",
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "metrics": metrics,
    }
    report = {
        "version": version,
        "selected_model": selected_name,
        "dataset_fingerprint": source_fingerprint,
        "quality": quality,
        "split": {"train_rows": int(len(X_train)), "test_rows": int(len(X_test)), "test_fraction": 0.2, "strategy": split_strategy},
        "selection_method": "Lowest mean 5-fold cross-validation MAE on training split",
        "held_out_test_metrics": metrics,
        "candidate_comparison": comparison,
        "limitations": [
            "This is a candidate artifact and does not replace the live model.",
            "Verify dataset provenance, consent/legal basis, target meaning, and representativeness before use.",
            "Held-out metrics describe this dataset and split only; they do not guarantee future or institutional performance.",
            "Review subgroup errors, calibration where relevant, and leakage before production promotion.",
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
        "live_model_replaced": False,
    }, indent=2))


if __name__ == "__main__":
    main()
