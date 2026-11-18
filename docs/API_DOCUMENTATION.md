# API Documentation

Interactive Swagger documentation is available at `/docs`.

Key endpoint groups:

- Authentication: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`
- Student: `/api/student/dashboard`, `/api/student/profile`
- Predictions: `/api/predictions/predict`, `/api/predictions/history`, `/api/predictions/{id}`
- Analytics: `/api/analytics/performance`, `/api/analytics/subjects`, `/api/analytics/trends`
- Recommendations: `/api/recommendations`
- Administration: `/api/admin/dashboard`, `/api/admin/users`, `/api/admin/predictions`, `/api/admin/models`, `/api/admin/analytics`, `/api/admin/audit-logs`

Protected endpoints require `Authorization: Bearer <token>`.
