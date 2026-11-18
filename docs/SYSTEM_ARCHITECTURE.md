# System Architecture

The React SPA communicates with FastAPI through a configurable REST API. FastAPI handles validation, JWT authentication, role authorization, SQLAlchemy persistence, analytics, and the ML inference service. SQLite is the default local database; PostgreSQL can be selected through `DATABASE_URL`.
