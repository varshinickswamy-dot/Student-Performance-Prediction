import os
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.models import AuditLog, Prediction, User
from app.schemas import (
    LoginRequest, PredictionInput, PredictionResponse, ProfileUpdate,
    RegisterRequest, PredictionSimulationInput, TokenResponse, UserResponse,
)
from app.core.security import (
    JWT_ALGORITHM, JWT_SECRET_KEY, create_access_token,
    hash_password, verify_password,
)
from app.ml.predictor import explain_prediction, predict, train
from app.ml.recommendations import build_recommendations, performance_category

router = APIRouter()


def public_user(user: User) -> dict:
    return {
        "id": user.id, "full_name": user.full_name, "email": user.email,
        "role": user.role, "active": user.active,
    }


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="Account unavailable")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


@router.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match")
    if db.query(User).filter(func.lower(User.email) == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email address is already registered")
    user = User(
        full_name=payload.full_name, email=payload.email.lower(),
        password_hash=hash_password(payload.password), role="student",
        student_id=payload.student_id, institution_name=payload.institution_name,
        department=payload.department, course=payload.course,
        semester=payload.semester, academic_year=payload.academic_year,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(AuditLog(actor_id=user.id, action="user_registered"))
    db.commit()
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token, user=public_user(user))


@router.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    db.add(AuditLog(actor_id=user.id, action="user_login"))
    db.commit()
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token, user=public_user(user))


@router.post("/api/auth/password-reset/request")
def password_reset_request(payload: dict):
    raise HTTPException(
        status_code=503,
        detail="Password reset is unavailable because no email delivery workflow is configured.",
    )


@router.post("/api/admin/login")
def admin_login(payload: dict, db: Session = Depends(get_db)):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()
    expected_username = os.getenv("ADMIN_USERNAME", "admin")
    if username != expected_username:
        raise HTTPException(status_code=401, detail="Invalid administrator credentials")
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin or not verify_password(password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid administrator credentials")
    db.add(AuditLog(actor_id=admin.id, action="admin_login"))
    db.commit()
    token = create_access_token(str(admin.id), admin.role)
    return TokenResponse(access_token=token, user=public_user(admin))


@router.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return public_user(user)


@router.get("/api/student/dashboard")
def student_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    predictions = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).all()
    latest = predictions[0] if predictions else None
    attendance = latest.input_data.get("attendance", 0) if latest else 0
    chronological = list(reversed(predictions))
    if len(chronological) >= 2:
        change = chronological[-1].predicted_score - chronological[-2].predicted_score
        improvement_trend = f"{change:+.1f}%"
    else:
        improvement_trend = "Insufficient history"
    return {
        "welcome_name": user.full_name,
        "total_assessments": len(predictions),
        "latest_predicted_score": latest.predicted_score if latest else None,
        "academic_performance_level": latest.performance_category if latest else None,
        "attendance_percentage": attendance,
        "improvement_trend": improvement_trend,
        "recommendations": latest.recommendations if latest else [],
        "recent_predictions": [
            {
                "id": p.id, "created_at": p.created_at.isoformat(), "subject": p.subject,
                "predicted_score": p.predicted_score, "performance_category": p.performance_category,
            } for p in predictions[:5]
        ],
    }


@router.get("/api/student/profile")
def student_profile(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("/api/student/profile")
def update_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/api/predictions/predict")
def create_prediction(
    payload: PredictionInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    score, artifact = predict(data)
    category = performance_category(score)
    recommendations = build_recommendations(data)
    prediction = Prediction(
        user_id=user.id, subject=payload.subject, semester=payload.semester,
        predicted_score=score, performance_category=category,
        input_data=data, recommendations=recommendations,
        model_version=artifact["version"],
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return PredictionResponse.model_validate(prediction)


@router.post("/api/predictions/simulate")
def simulate_prediction(
    payload: PredictionSimulationInput,
    user: User = Depends(get_current_user),
):
    """Compare two scenarios with the same deployed model without saving either result."""
    if (
        payload.baseline.subject.strip().casefold() != payload.scenario.subject.strip().casefold()
        or payload.baseline.semester.strip().casefold() != payload.scenario.semester.strip().casefold()
    ):
        raise HTTPException(
            status_code=422,
            detail="Baseline and scenario must use the same subject and semester.",
        )

    baseline_score, artifact = predict(payload.baseline.model_dump())
    scenario_score, scenario_artifact = predict(payload.scenario.model_dump())
    if artifact["version"] != scenario_artifact["version"]:
        raise HTTPException(status_code=503, detail="The prediction model changed during simulation. Please retry.")

    return {
        "baseline_score": baseline_score,
        "scenario_score": scenario_score,
        "change": round(scenario_score - baseline_score, 1),
        "model_version": artifact["version"],
        "dataset": artifact["dataset"],
        "is_synthetic_demo": "synthetic" in artifact["dataset"].lower(),
        "saved": False,
        "disclaimer": "This is a scenario comparison from the currently deployed model, not a guaranteed academic outcome.",
    }


@router.get("/api/predictions/history")
def prediction_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = None,
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Prediction).filter(Prediction.user_id == user.id)
    if search:
        query = query.filter(Prediction.subject.ilike(f"%{search}%"))
    if category:
        query = query.filter(Prediction.performance_category == category)
    total = query.count()
    items = query.order_by(Prediction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [PredictionResponse.model_validate(p).model_dump(mode="json") for p in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/api/predictions/{prediction_id}")
def prediction_detail(prediction_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prediction = db.get(Prediction, prediction_id)
    if not prediction or prediction.user_id != user.id:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return PredictionResponse.model_validate(prediction)


@router.get("/api/predictions/{prediction_id}/explanation")
def prediction_explanation(
    prediction_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prediction = db.get(Prediction, prediction_id)
    if not prediction or prediction.user_id != user.id:
        raise HTTPException(status_code=404, detail="Prediction not found")

    explanation = explain_prediction(prediction.input_data)
    if explanation["version"] != prediction.model_version:
        raise HTTPException(
            status_code=409,
            detail="The saved prediction uses a different model version. A matching explanation is unavailable.",
        )

    return {
        "prediction_id": prediction.id,
        "model_version": explanation["version"],
        "dataset": explanation["dataset"],
        "baseline_score": explanation["baseline_score"],
        "raw_model_output": explanation["raw_model_output"],
        "predicted_score": explanation["predicted_score"],
        "method": explanation["method"],
        "is_causal": explanation["is_causal"],
        "contributions": explanation["contributions"],
        "disclaimer": (
            "Contributions describe how this Ridge model uses each input relative to "
            "training feature means. They are not causal effects or proof of real-world "
            "student outcomes. The current repository model uses synthetic demonstration data."
        ),
    }


@router.delete("/api/predictions/{prediction_id}", status_code=204)
def delete_prediction(prediction_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prediction = db.get(Prediction, prediction_id)
    if not prediction or prediction.user_id != user.id:
        raise HTTPException(status_code=404, detail="Prediction not found")
    db.delete(prediction)
    db.commit()
    return None


@router.get("/api/recommendations")
def recommendations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    latest = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).first()
    return latest.recommendations if latest else []


@router.get("/api/analytics/performance")
def analytics_performance(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at).all()
    return [{"date": p.created_at.date().isoformat(), "score": p.predicted_score, "subject": p.subject} for p in items]


@router.get("/api/analytics/subjects")
def analytics_subjects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Prediction.subject, func.avg(Prediction.predicted_score)).filter(
        Prediction.user_id == user.id
    ).group_by(Prediction.subject).all()
    return [{"subject": subject, "score": round(float(avg), 1)} for subject, avg in rows]


@router.get("/api/analytics/trends")
def analytics_trends(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at).all()
    return [
        {"date": p.created_at.strftime("%Y-%m-%d"), "score": p.predicted_score,
         "attendance": p.input_data.get("attendance", 0),
         "study_hours": p.input_data.get("study_hours", 0)}
        for p in items
    ]


@router.get("/api/admin/dashboard")
def admin_dashboard(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role == "student").count()
    predictions = db.query(Prediction).count()
    active = db.query(User).filter(User.active == True).count()
    average = db.query(func.avg(Prediction.predicted_score)).scalar()
    categories = db.query(Prediction.performance_category, func.count(Prediction.id)).group_by(
        Prediction.performance_category
    ).all()
    recent_users = db.query(User).filter(User.role == "student").order_by(User.created_at.desc()).limit(5).all()
    recent_predictions = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(5).all()
    return {
        "total_students": users, "total_predictions": predictions,
        "active_users": active, "average_score": round(float(average or 0), 1),
        "category_distribution": [{"name": name, "value": count} for name, count in categories],
        "recent_student_registrations": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "created_at": u.created_at.isoformat(),
            }
            for u in recent_users
        ],
        "recent_prediction_activities": [
            {
                "id": p.id,
                "student_name": p.user.full_name,
                "subject": p.subject,
                "predicted_score": p.predicted_score,
                "created_at": p.created_at.isoformat(),
            }
            for p in recent_predictions
        ],
    }


@router.get("/api/admin/users")
def admin_users(search: str | None = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = db.query(User).filter(User.role == "student")
    if search:
        query = query.filter(User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
    return [UserResponse.model_validate(u).model_dump(mode="json") for u in query.order_by(User.created_at.desc()).all()]


@router.patch("/api/admin/users/{user_id}/active")
def set_user_active(user_id: int, active: bool, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user or user.role == "admin":
        raise HTTPException(status_code=404, detail="Student not found")
    user.active = active
    db.commit()
    return {"id": user.id, "active": user.active}


@router.get("/api/admin/predictions")
def admin_predictions(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    items = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(500).all()
    result = []
    for p in items:
        result.append({
            "id": p.id, "student_name": p.user.full_name, "subject": p.subject,
            "predicted_score": p.predicted_score, "performance_category": p.performance_category,
            "created_at": p.created_at.isoformat(),
        })
    return result


@router.get("/api/admin/models")
def admin_models(admin: User = Depends(require_admin)):
    artifact = train()
    return {
        "version": artifact["version"], "dataset": artifact["dataset"],
        "training_rows": artifact["training_rows"], "test_rows": artifact["test_rows"],
        "metrics": artifact["metrics"], "features": artifact["features"],
        "model_type": "Ridge regression",
        "is_synthetic_demo": "synthetic" in artifact["dataset"].lower(),
        "evaluation_note": "Metrics are measured on a held-out split of the documented dataset; synthetic-demo metrics are not evidence of real-world student performance.",
    }


@router.get("/api/admin/analytics")
def admin_analytics(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    predictions = db.query(Prediction).all()
    return {
        "subject_performance": [
            {"subject": subject, "score": round(float(avg), 1)}
            for subject, avg in db.query(Prediction.subject, func.avg(Prediction.predicted_score)).group_by(Prediction.subject).all()
        ],
        "prediction_trend": [
            {"date": p.created_at.strftime("%Y-%m-%d"), "score": p.predicted_score}
            for p in sorted(predictions, key=lambda item: item.created_at)[-30:]
        ],
    }


@router.get("/api/admin/audit-logs")
def audit_logs(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return [{"id": l.id, "actor_id": l.actor_id, "action": l.action, "details": l.details, "created_at": l.created_at.isoformat()} for l in logs]


@router.delete("/api/admin/users/{user_id}", status_code=204)
def delete_student(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user or user.role == "admin":
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(user)
    db.add(AuditLog(actor_id=admin.id, action="student_deleted", details=f"Student ID {user_id}"))
    db.commit()
    return None


@router.get("/api/admin/settings")
def admin_settings(admin: User = Depends(require_admin)):
    return {
        "application_name": "EduPredict",
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "email_reset_provider_configured": bool(os.getenv("EMAIL_PROVIDER")),
        "default_admin_username": os.getenv("ADMIN_USERNAME", "admin"),
    }


@router.post("/api/admin/change-password")
def admin_change_password(
    payload: dict,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    current_password = str(payload.get("current_password", ""))
    new_password = str(payload.get("new_password", ""))
    if not verify_password(current_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(new_password) < 12:
        raise HTTPException(status_code=422, detail="New password must contain at least 12 characters")
    admin.password_hash = hash_password(new_password)
    db.add(AuditLog(actor_id=admin.id, action="admin_password_changed"))
    db.commit()
    return {"status": "updated"}
