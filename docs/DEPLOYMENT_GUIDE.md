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

Set `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `FRONTEND_URL=https://student-performance-prediction-amber.vercel.app`. Use a persistent PostgreSQL database for production.


## Health and readiness checks

- `GET /api/health` is the backward-compatible liveness response.
- `GET /api/health/live` confirms that the process can answer requests.
- `GET /api/health/ready` checks both the configured database connection and the persisted/trained ML pipeline. It returns HTTP 503 if either dependency is unavailable.

After a backend deployment, verify both the existing health endpoint and readiness endpoint. Do not treat a successful liveness response alone as proof that PostgreSQL is connected.

## Prediction explainability and what-if API

- `GET /api/predictions/{prediction_id}/explanation` requires the owning student's JWT. It returns an additive decomposition from the same Ridge artifact used for the saved prediction. A model-version mismatch returns HTTP 409 rather than presenting a misleading explanation.
- `POST /api/predictions/simulate` accepts `baseline` and `scenario` objects with the existing prediction input schema. Subject and semester must match. The endpoint does not create database records and returns a clear model/dataset disclaimer.
