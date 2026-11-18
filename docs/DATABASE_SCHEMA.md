# Database Schema

- `users`: authentication, profile, role, and account status
- `predictions`: owned by a user and stores input, estimate, category, recommendations, and model version
- `audit_logs`: security and account activity

Foreign keys, indexes, timestamps, and SQLAlchemy relationships are defined in `backend/app/models.py`.
