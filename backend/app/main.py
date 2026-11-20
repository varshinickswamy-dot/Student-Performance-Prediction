import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.database import Base, engine, SessionLocal
from app.models import User
from app.core.security import hash_password
from app.ml.predictor import train
from sqlalchemy import text

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student Performance Prediction API",
    version="1.0.0",
    description="AI-powered student performance prediction and academic analytics.",
)

# Keep every active first-party frontend hostname explicitly allowlisted.
# FRONTEND_URL can add deployment aliases, but must not accidentally remove
# the current Vercel project domain when Render has a narrower env value.
configured_frontend_origins = os.getenv("FRONTEND_URL", "")
frontend_origins = ",".join(filter(None, [
    configured_frontend_origins,
    "https://varshinickswamy-dots-projects.vercel.app",
    "https://student-performance-prediction-amber.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(router)


@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "admin123")
        if os.getenv("ENVIRONMENT", "development").lower() in {"production", "prod"}:
            if not os.getenv("FRONTEND_URL"):
                raise RuntimeError("FRONTEND_URL must be configured in production.")
            if not os.getenv("ADMIN_PASSWORD") or password == "admin123":
                raise RuntimeError("Set a non-default ADMIN_PASSWORD before production startup.")
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            db.add(User(
                full_name="System Administrator", email=f"{username}@local.admin",
                password_hash=hash_password(password), role="admin",
            ))
            db.commit()
        train()
    finally:
        db.close()


@app.get("/api/health")
def health():
    # Backward-compatible liveness response used by existing deployment checks.
    return {"status": "ok", "model": "available"}


@app.get("/api/health/live")
def liveness():
    return {"status": "alive"}


@app.get("/api/health/ready")
def readiness():
    """Check the dependencies required to serve authenticated predictions."""
    checks = {"database": "unavailable", "model": "unavailable"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = "available"
    except Exception:
        pass

    try:
        artifact = train()
        checks["model"] = "available"
        checks["model_version"] = artifact.get("version", "unknown")
        checks["dataset"] = artifact.get("dataset", "unknown")
    except Exception:
        pass

    if checks["database"] != "available" or checks["model"] != "available":
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}
