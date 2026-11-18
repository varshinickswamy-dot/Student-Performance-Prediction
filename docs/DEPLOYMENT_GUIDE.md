# Deployment Guide

## Frontend

Import the `frontend/` directory into Vercel. Set `VITE_API_BASE_URL` to the backend HTTPS URL and deploy. `vercel.json` provides SPA routing.

## Backend

Deploy `backend/` to Render, Railway, or another ASGI-capable platform. Use Python 3.12 and start with:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `FRONTEND_URL`. Use a persistent PostgreSQL database for production.
