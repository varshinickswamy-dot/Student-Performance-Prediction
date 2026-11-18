# EduPredict - Student Performance Prediction

EduPredict is a full-stack academic analytics application for student performance prediction. It includes a React dashboard, FastAPI backend, SQLite/PostgreSQL database support, JWT authentication, role-based administration, and a real scikit-learn Ridge regression model.

## Features

- Premium responsive public website with dark and light themes
- Registration, login, protected student routes, and JWT sessions
- Demonstration Ridge regression model with persisted Joblib artifact
- Prediction history, delete protection, analytics, and transparent recommendations
- Student profile management
- Role-based administrator dashboard and audit logs
- Vercel-compatible frontend and independently deployable FastAPI backend
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

## Administrator login

- Username: `admin`
- Password: `admin123`

The initial demonstration credentials are configurable with `ADMIN_USERNAME` and `ADMIN_PASSWORD`. Change the password before deployment. Stored passwords are PBKDF2-hashed; the initial value is never stored as plain text.

## Model methodology

The demo Ridge regression pipeline uses study hours, previous marks, attendance, assignment scores, class participation, homework completion, sleep hours, extracurricular activity, internet access, and family support. The synthetic data and target are generated deterministically with random seed 42. The model uses an 80/20 train/test split.

The actual evaluation metrics are exposed by `GET /api/admin/models`. No fixed or promised accuracy is used.

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
- Set Render `FRONTEND_URL` to `https://student-performance-prediction-amber.vercel.app`.
- Set `ENVIRONMENT=production`; startup rejects the development JWT secret, missing frontend origin, and default administrator password.
- Never commit `.env` files or secrets.

See the documents in `docs/`.
