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


## New academic intelligence and role workflows

The latest backend adds additive tables for study goals, teacher/student assignments, teacher intervention notes, and student activity logs. Startup uses SQLAlchemy `create_all` to create missing tables; it does not drop or reset existing user, prediction, or audit data. Confirm the Render database account has permission to create tables. For future changes to existing columns, use a reviewed migration rather than relying on `create_all`.

New student endpoints include:

- `GET /api/student/risk-assessment`
- `POST /api/student/study-plan`
- `GET /api/student/notifications`
- `GET/POST /api/student/goals`
- `PATCH/DELETE /api/student/goals/{goal_id}`
- `GET/POST /api/student/activities`
- `GET /api/student/activities/summary`
- `DELETE /api/student/activities/{activity_id}`
- `GET /api/analytics/heatmap`
- `GET /api/analytics/semester-comparison`
- `POST /api/assistant/chat`

Teacher and institution workflows:

- System administrators create teacher accounts with `POST /api/admin/teachers` and institution administrators with `POST /api/admin/institution-admins`.
- Assign students using `POST /api/admin/teachers/{teacher_id}/assignments`. The API requires matching institution names.
- Teacher routes expose only assigned students and assigned-student intervention notes.
- Institution administrators receive institution-filtered aggregate model-estimate analytics.
- The system administrator can list staff using `GET /api/admin/teaching-staff`.

The assistant works without an external provider using a contextual built-in fallback. To enable an OpenAI-compatible provider, configure `AI_API_KEY`, `AI_MODEL`, and optionally `AI_API_BASE_URL` as Render environment variables. Keep the key server-side only; production provider URLs must use HTTPS. If these values are not configured or the provider is unavailable, the built-in fallback remains active. The student-facing assistant requires a separate explicit consent checkbox for each request before any external call. Only the question and limited academic context are sent; the student's name and account ID are excluded. Review the provider's data handling and applicable notice/consent requirements before enabling it.

The academic support assessment uses explicit rules and recorded model estimates. It returns support points, not calibrated probabilities. Student-entered activity logs are self-reported and must not be treated as official attendance or institutional grade records.
