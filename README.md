# EduPredict - Student Performance Prediction

## 🚀 Live Demo

**Frontend:** [Open EduPredict](https://student-performance-prediction-amber.vercel.app)

**Backend API:** [Open API Health Check](https://student-performance-backend-nujh.onrender.com/api/health) · [API Documentation](https://student-performance-backend-nujh.onrender.com/docs)

EduPredict is a full-stack academic analytics application for student performance prediction. It includes a React dashboard, FastAPI backend, SQLite/PostgreSQL database support, JWT authentication, role-based administration, and a real scikit-learn Ridge regression model.

## Features

- Premium responsive public website with dark and light themes
- Student registration and login, protected student routes, and JWT sessions
- Demonstration Ridge regression model with persisted Joblib artifact
- Prediction history, delete protection, analytics, and transparent recommendations
- Authenticated model explanations using additive Ridge coefficient contributions
- What-if scenario comparisons using the same deployed prediction pipeline without saving simulated records
- Separate liveness and dependency-readiness endpoints for deployment monitoring
- Student profile management
- Rule-based academic support assessment with transparent factors (not a validated probability)
- Seven-day personalized study planner based on the student's latest saved inputs
- Persistent study goals with completion tracking
- Student-entered study-session, attendance and assignment activity tracker with 7-day/30-day summaries
- Subject-by-semester heatmap and semester comparison analytics
- Contextual academic assistant with a built-in fallback and optional server-side OpenAI-compatible provider
- Dynamic notifications for support indicators and upcoming/overdue study goals
- Role-separated teacher and institution workspaces with assigned-student isolation and intervention notes
- Role-based administrator dashboard, teacher account provisioning, student assignment management, and audit logs
- Vercel-compatible frontend and independently deployable FastAPI backend
- Separate final-exam candidate estimator UI at `/final-exam`, backed by an authenticated, opt-in API; it never replaces the original deployed model
- Prediction report download and paginated history
- Downloadable, formatted PDF prediction reports
- Administrator audit logs, settings, password management, exports, and student safeguards

## Repository status

The original GitHub repository was empty, and no dataset or existing implementation was available. The demo model therefore trains on a seeded synthetic dataset. It is explicitly documented and must not be presented as evidence for real students.

## Technology

- Frontend: React, Vite, Recharts, React Router, Lucide, Framer Motion
- Backend: Python, FastAPI, SQLAlchemy, Pydantic, PyJWT
- Machine learning: NumPy, Pandas, scikit-learn, Joblib
- Database: SQLite locally; PostgreSQL in production

## Local setup

### Backend

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="sqlite:///./student_performance.db"
$env:JWT_SECRET_KEY="replace-with-a-random-secret"
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="admin123"
uvicorn app.main:app --reload --port 8000
```

API documentation: http://localhost:8000/docs

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open http://localhost:5173.

## Local administrator setup

For local development only, configure `ADMIN_USERNAME` and a strong `ADMIN_PASSWORD` in your untracked backend `.env` file. The application hashes the configured password before storage. Do not publish administrator credentials or reuse local credentials in production. Production startup rejects the default demonstration password.

## Model methodology

The demo Ridge regression pipeline uses study hours, previous marks, attendance, assignment scores, class participation, homework completion, sleep hours, extracurricular activity, internet access, and family support. The synthetic data and target are generated deterministically with random seed 42. The model uses an 80/20 train/test split.

The actual evaluation metrics are exposed by `GET /api/admin/models`. An offline candidate comparison command is available as `python -m app.ml.train_candidate`; it requires an authorized CSV path and saves a candidate artifact separately without replacing the deployed model. The current artifact is explicitly identified as a synthetic demonstration model; its metrics are not evidence of real-world student performance. No fixed or promised accuracy is used.

The API also exposes `GET /api/predictions/{prediction_id}/explanation` for authenticated, owner-scoped additive Ridge coefficient contributions and `POST /api/predictions/simulate` for non-persisted what-if comparisons. These use the same deployed artifact as ordinary predictions. See [ML methodology](docs/ML_METHODOLOGY.md) for interpretation and limitations.

## Testing

```powershell
py -3.12 -m pytest tests -q
cd frontend
npm run build
```

## Deployment

- Deploy `frontend/` to Vercel.
- Set the Vercel environment variable `VITE_API_BASE_URL` to `https://student-performance-backend-nujh.onrender.com`.
- Deploy `backend/` to a compatible Python host such as Render or Railway.
- Set `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` in Render.
- Set Render `FRONTEND_URL` to your active Vercel deployment origin(s), comma-separated. The backend also explicitly allows the current project domain `https://varshinickswamy-dots-projects.vercel.app` and the earlier production alias.
- Set `ENVIRONMENT=production`; startup rejects the development JWT secret, missing frontend origin, and default administrator password.
- Never commit `.env` files or secrets.

See [deployment guide](docs/DEPLOYMENT_GUIDE.md), [ML methodology and candidate training](docs/ML_METHODOLOGY.md), and [Android integration guide](docs/ANDROID_INTEGRATION.md).


## Academic Growth Lab

The authenticated student workspace at `/growth-lab` adds a descriptive Digital Twin snapshot, a four-week recovery checklist, an exam preparation schedule, a topic-based practice prompt generator, a transparent career skill-map checklist, and exploratory scholarship pathway screening. These features use the signed-in student's own records or explicit self-reported form inputs. They do not retrain or replace the deployed Ridge model.

Staff intelligence endpoints are role-protected: `GET /api/teacher/intelligence` includes only assigned students; `GET /api/institution/intelligence` returns institution aggregates and suppresses department/semester groups smaller than five.

Important limitations: career readiness is a small illustrative skill-map coverage measure, not a hiring probability. Scholarship results are potential pathways, not verified live awards or eligibility decisions. Practice questions are generated prompts, not actual or leaked exam questions. See [Academic Growth Lab guide](docs/ACADEMIC_GROWTH_LAB.md).


## ML validation upgrades

The offline candidate trainer now audits dataset missingness, duplicates, feature/target distributions, constant features, and unusually high correlations for human leakage review. It rejects unsupported boolean values, supports group-isolated student-level holdout and cross-validation, compares candidate models against a mean baseline, and records expanded held-out regression metrics and residual diagnostics.

This remains an offline candidate workflow. It does not retrain or replace the deployed synthetic demonstration model. No real authorized student dataset is currently present in the repository; a dataset owner must provide one with documented provenance and permission before a real-world model can be evaluated.


## Synthetic student dataset candidate benchmark

An anonymized generated CSV can be evaluated offline with `python -m app.ml.train_student_candidate` after setting `EDUPREDICT_STUDENT_DATASET_PATH`. This candidate predicts `final_exam_score` from pre-final academic inputs, excludes IDs/demographics/derived outcomes, and uses student-group-isolated evaluation. It is deliberately separate from the deployed Ridge model because its feature contract differs. See [Synthetic Dataset Benchmark](docs/SYNTHETIC_DATASET_BENCHMARK.md). No Render environment change or production model promotion is required.


## Final-exam candidate estimator

The student workspace includes a separate estimator at `/final-exam`. It sends the ten pre-final features to the authenticated `POST /api/student/final-exam-prediction` endpoint. The API validates the candidate artifact's feature contract and synthetic-data provenance before inference.

To enable this optional endpoint on a backend host, first create and review the local candidate using the instructions in [Synthetic Dataset Benchmark](docs/SYNTHETIC_DATASET_BENCHMARK.md), then securely provide the candidate Joblib artifact to the backend and set `EDUPREDICT_STUDENT_CANDIDATE_ARTIFACT` to its absolute path. Do not commit the artifact or the source CSV. If the variable or file is absent, the endpoint returns HTTP 503 with a clear message; it does not generate a placeholder prediction. The UI therefore remains safely unavailable until the reviewed artifact is configured.

Every returned score is labelled as a synthetic demonstration estimate. It is not validated for real students and must not be used for grading, admissions, scholarship, disciplinary, or other high-impact decisions.


## Project report

The complete academic project report covers the system architecture, requirements, implementation, model methodology, limitations, testing plan, deployment and appendices. The report is maintained as a separate submission artifact; add the final reviewed PDF to the repository only if you want it publicly downloadable.
