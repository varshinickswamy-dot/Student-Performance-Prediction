# Deployment Guide

## Frontend

Import the `frontend/` directory into Vercel. Set this environment variable and deploy:

```text
VITE_API_BASE_URL=https://student-performance-backend-nujh.onrender.com
```

`vercel.json` provides SPA routing.

## Backend

Deploy `backend/` to Render, Railway, or another ASGI-capable platform. Set the backend root directory to `backend/` and use Python 3.12.

Render build command:

```text
python -m pip install --upgrade pip && python -m pip install --only-binary=:all: -r requirements.txt
```

This installs prebuilt wheels only; it prevents pip from silently attempting to compile packages from source.

Start command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `FRONTEND_URL=https://student-performance-prediction-flax-eight.vercel.app`. Use a persistent PostgreSQL database for production.
