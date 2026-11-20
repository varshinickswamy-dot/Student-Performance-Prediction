import os
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ARTIFACT_DIR = Path(__file__).resolve().parent / "model_artifacts"
MODEL_PATH = ARTIFACT_DIR / "ridge_model.joblib"
FEATURES = [
    "study_hours", "previous_marks", "attendance", "assignment_scores",
    "class_participation", "homework_completion", "sleep_hours",
    "extracurricular", "internet_access", "family_support",
]


def synthetic_training_frame(rows: int = 1200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    study = rng.normal(4.5, 2.0, rows).clip(0, 12)
    previous = rng.normal(68, 15, rows).clip(20, 100)
    attendance = rng.normal(82, 12, rows).clip(40, 100)
    assignments = rng.normal(70, 14, rows).clip(20, 100)
    participation = rng.normal(65, 18, rows).clip(10, 100)
    homework = rng.normal(78, 16, rows).clip(20, 100)
    sleep = rng.normal(7.2, 1.2, rows).clip(4, 10)
    extracurricular = rng.integers(0, 2, rows)
    internet = rng.integers(0, 2, rows)
    support = rng.integers(0, 2, rows)
    score = (
        18 + study * 2.4 + previous * 0.32 + attendance * 0.14
        + assignments * 0.16 + participation * 0.05 + homework * 0.08
        + (sleep - 7).clip(-3, 3) * 0.35 + extracurricular * 0.8
        + internet * 1.2 + support * 1.5
    )
    score = (score + rng.normal(0, 5, rows)).clip(0, 100)
    return pd.DataFrame({
        "study_hours": study, "previous_marks": previous, "attendance": attendance,
        "assignment_scores": assignments, "class_participation": participation,
        "homework_completion": homework, "sleep_hours": sleep,
        "extracurricular": extracurricular, "internet_access": internet,
        "family_support": support, "score": score,
    })


def train(force: bool = False):
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists() and not force:
        return joblib.load(MODEL_PATH)
    df = synthetic_training_frame()
    X = df[FEATURES]
    y = df["score"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=1.0)),
    ])
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    metrics = {
        "mae": float(mean_absolute_error(y_test, predictions)),
        "mse": float(mean_squared_error(y_test, predictions)),
        "rmse": float(mean_squared_error(y_test, predictions) ** 0.5),
        "r2": float(r2_score(y_test, predictions)),
    }
    artifact = {
        "pipeline": pipeline,
        "features": FEATURES,
        "metrics": metrics,
        "version": "demo-ridge-v1",
        "dataset": "Seeded synthetic demonstration dataset",
        "training_rows": len(X_train),
        "test_rows": len(X_test),
    }
    joblib.dump(artifact, MODEL_PATH)
    return artifact


def _feature_frame(data: dict) -> pd.DataFrame:
    """Build the exact feature row expected by the persisted production pipeline."""
    return pd.DataFrame([{
        key: (1 if data[key] else 0) if key in {
            "extracurricular", "internet_access", "family_support"
        } else data[key]
        for key in FEATURES
    }])


def predict(data: dict) -> tuple[float, dict]:
    artifact = train()
    row = _feature_frame(data)
    score = float(artifact["pipeline"].predict(row)[0])
    return round(max(0.0, min(100.0, score)), 1), artifact


def explain_prediction(data: dict) -> dict:
    """
    Explain the deployed Ridge model with exact additive coefficient
    contributions relative to the training feature means.

    This is a model-specific linear decomposition, not SHAP and not a
    causal explanation. It deliberately uses the same persisted artifact
    as predict(), so explanations stay compatible with deployed predictions.
    """
    artifact = train()
    pipeline = artifact["pipeline"]
    scaler = pipeline.named_steps["scaler"]
    estimator = pipeline.named_steps["model"]
    row = _feature_frame(data)
    scaled_values = scaler.transform(row)[0]
    coefficients = np.asarray(estimator.coef_, dtype=float).reshape(-1)
    contributions = []

    for index, feature in enumerate(FEATURES):
        value = data[feature]
        contribution = float(scaled_values[index] * coefficients[index])
        contributions.append({
            "feature": feature,
            "value": value,
            "contribution": round(contribution, 4),
            "direction": "positive" if contribution > 0 else "negative" if contribution < 0 else "neutral",
        })

    contributions.sort(key=lambda item: abs(item["contribution"]), reverse=True)
    baseline = float(np.asarray(estimator.intercept_).reshape(-1)[0])
    raw_score = baseline + sum(item["contribution"] for item in contributions)
    return {
        "version": artifact["version"],
        "dataset": artifact["dataset"],
        "baseline_score": round(baseline, 4),
        "raw_model_output": round(raw_score, 4),
        "predicted_score": round(max(0.0, min(100.0, raw_score)), 1),
        "contributions": contributions,
        "method": "Ridge coefficient contributions relative to training feature means",
        "is_causal": False,
    }
