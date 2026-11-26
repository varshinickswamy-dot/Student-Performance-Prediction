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

Set `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FRONTEND_URL`, and `ENVIRONMENT=production`. `FRONTEND_URL` should contain every active frontend origin, comma-separated (for example `https://student-performance-prediction-amber.vercel.app,https://varshinickswamy-dots-projects.vercel.app`). Use a persistent PostgreSQL database for production. Generate a unique, high-entropy JWT secret and a strong non-default administrator password; never copy local demo credentials into production.


## Health and readiness checks

- `GET /api/health` is the backward-compatible liveness response.
- `GET /api/health/live` confirms that the process can answer requests.
- `GET /api/health/ready` checks both the configured database connection and the persisted/trained ML pipeline. It returns HTTP 503 if either dependency is unavailable.

After a backend deployment, verify `/api/health`, `/api/health/live`, and `/api/health/ready`. Do not treat a successful liveness response alone as proof that PostgreSQL and the model are ready. Also test registration, login, a protected prediction, history ownership, and the frontend-to-backend CORS preflight from the published domain.

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
- `GET /api/admin/model-monitoring` (system administrator only; exploratory input-distribution diagnostic)
- `POST /api/assistant/chat`

Teacher and institution workflows:

- System administrators create teacher accounts with `POST /api/admin/teachers` and institution administrators with `POST /api/admin/institution-admins`.
- Assign students using `POST /api/admin/teachers/{teacher_id}/assignments`. The API requires matching institution names.
- Teacher routes expose only assigned students and assigned-student intervention notes.
- Institution administrators receive institution-filtered aggregate model-estimate analytics.
- The system administrator can list staff using `GET /api/admin/teaching-staff`.

The assistant works without an external provider using a contextual built-in fallback. To enable an OpenAI-compatible provider, configure `AI_API_KEY`, `AI_MODEL`, and optionally `AI_API_BASE_URL` as Render environment variables. Keep the key server-side only; production provider URLs must use HTTPS. If these values are not configured or the provider is unavailable, the built-in fallback remains active. The student-facing assistant requires a separate explicit consent checkbox for each request before any external call. Only the question and limited academic context are sent; the student's name and account ID are excluded. Review the provider's data handling and applicable notice/consent requirements before enabling it.

The academic support assessment uses explicit rules and recorded model estimates. It returns support points, not calibrated probabilities. Student-entered activity logs are self-reported and must not be treated as official attendance or institutional grade records.


## Presentation-day production smoke test

The read-only smoke script checks the published frontend, backend liveness, backend readiness (database and model), and the Vercel-origin CORS preflight. It does not create accounts, modify records, or require secrets.

Run from the repository root:

```powershell
py -3.12 scripts/production_smoke.py
```

Optional overrides:

```powershell
$env:EDUPREDICT_FRONTEND_URL="https://your-active-vercel-domain"
$env:EDUPREDICT_API_URL="https://your-render-service"
py -3.12 scripts/production_smoke.py
```

A successful smoke test is necessary but not sufficient for release sign-off. Manually verify student registration/login, create a prediction, confirm it appears in history, download a report, and confirm a second student cannot access the first student's prediction. For staff demonstrations, use dedicated test accounts and verify each role only sees its permitted institution or assigned students. Never use real student personal data in a presentation.

If readiness fails, inspect Render logs and confirm the production variables listed above. If CORS fails, add the exact Vercel origin (scheme and hostname, without a trailing path) to `FRONTEND_URL` and redeploy the backend. Do not paste secrets into logs, screenshots, GitHub issues, or chat.
