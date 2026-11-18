import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.database import Base, engine, SessionLocal
from app.models import User
from app.core.security import hash_password
from app.ml.predictor import train

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student Performance Prediction API",
    version="1.0.0",
    description="AI-powered student performance prediction and academic analytics.",
)

frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173,http://127.0.0.1:5173",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_url.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "ok", "model": "available"}
