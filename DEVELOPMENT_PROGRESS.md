# Development Progress

## Implemented in the repository

- React/Vite public site and authenticated student application with responsive dark/light themes.
- FastAPI backend with JWT authentication, password hashing, role-based authorization and SQLAlchemy persistence.
- SQLite local support and PostgreSQL production configuration.
- Persisted Ridge regression demonstration model with deterministic synthetic-data provenance.
- Prediction creation, paginated history, analytics, reports, explanations and non-persisted what-if simulation.
- Student profile, study planner, goals, notifications, self-reported activity tracking and academic analytics.
- Academic Growth Lab with recovery checklist, exam preparation, practice prompts, career skill maps and scholarship pathway screening.
- Teacher and institution workspaces with assignment/institution scoping and small-cohort suppression.
- System administration, teacher provisioning, student assignments, audit logs and model monitoring.
- Separate optional final-exam candidate endpoint and UI; it fails closed when the candidate artifact is not configured and does not replace the baseline model.
- Backend pytest suite and GitHub Actions workflow for backend tests and frontend production build.
- Production email-verification workflow for new student registrations using Resend, with expiring one-time tokens, resend throttling and login gating; legacy accounts and staff provisioned by administrators remain compatible.
- Deployment, API, architecture, ML methodology, dataset benchmark and feature documentation.
- README includes published frontend, backend health and API documentation links.

## Latest documentation maintenance

- Added a production-only email-verification flow for new student registrations. Verification tokens are hashed at rest, expire after 30 minutes, and can be reissued with a 60-second cooldown. Existing accounts without verification records are not locked out.


- Clarified local-only administrator setup and removed public default credential instructions.
- Corrected escaped newline formatting in README feature bullets.
- Clarified production environment variables, active frontend origins, strong secrets and post-deployment smoke checks.
- Added a pointer to the separate academic project report artifact.

## Remaining tasks requiring owner action or live verification

1. Restore/verify Render environment variables and confirm the backend starts in production. Required values include `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FRONTEND_URL`, and `ENVIRONMENT=production`.
2. Confirm the Render PostgreSQL database is persistent and that existing records remain intact.
3. Verify `/api/health/ready` returns ready; then test registration, login, prediction, history, and CORS from the published Vercel site.
4. Confirm Vercel uses the correct `VITE_API_BASE_URL` and redeploys the latest main branch.
5. Configure `RESEND_API_KEY` and a verified-domain `EMAIL_FROM` sender in Render; test new registration, inbox delivery, verification, expired-link handling, resend throttling and login gating. Password reset remains a separate workflow and is not enabled by email verification.
6. Supply an authorised, documented real student dataset before attempting real-world model evaluation. The current model is synthetic demonstration data only.
7. Keep the final-exam candidate optional unless its artifact is securely hosted and reviewed. Do not commit private CSVs or Joblib artifacts.
8. Run the CI workflow and resolve any failing checks before declaring release complete.
9. If the academic report should be public, add the reviewed PDF to the repository as a separate release/document asset.

## Release limitations

- The synthetic baseline is not validated for real students and must not be used for grading, admissions, scholarship, discipline or other high-impact decisions.
- Career skill-map percentages and scholarship pathways are exploratory, not hiring probabilities or verified eligibility.
- Student-entered activity is self-reported, not official institutional data.
- A published URL alone does not prove current service health; the live smoke checks above remain outstanding.
