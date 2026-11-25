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
- Deployment, API, architecture, ML methodology, dataset benchmark and feature documentation.
- README includes published frontend, backend health and API documentation links.

## Latest documentation maintenance

- Clarified local-only administrator setup and removed public default credential instructions.
- Corrected escaped newline formatting in README feature bullets.
- Clarified production environment variables, active frontend origins, strong secrets and post-deployment smoke checks.
- Added a pointer to the separate academic project report artifact.

## Remaining tasks requiring owner action or live verification

1. Restore/verify Render environment variables and confirm the backend starts in production. Required values include `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FRONTEND_URL`, and `ENVIRONMENT=production`.
2. Confirm the Render PostgreSQL database is persistent and that existing records remain intact.
3. Verify `/api/health/ready` returns ready; then test registration, login, prediction, history, and CORS from the published Vercel site.
4. Confirm Vercel uses the correct `VITE_API_BASE_URL` and redeploys the latest main branch.
5. Configure password-reset email delivery only if that feature is required; otherwise keep the honest unavailable response.
6. Supply an authorised, documented real student dataset before attempting real-world model evaluation. The current model is synthetic demonstration data only.
7. Keep the final-exam candidate optional unless its artifact is securely hosted and reviewed. Do not commit private CSVs or Joblib artifacts.
8. Run the CI workflow and resolve any failing checks before declaring release complete.
9. If the academic report should be public, add the reviewed PDF to the repository as a separate release/document asset.

## Release limitations

- The synthetic baseline is not validated for real students and must not be used for grading, admissions, scholarship, discipline or other high-impact decisions.
- Career skill-map percentages and scholarship pathways are exploratory, not hiring probabilities or verified eligibility.
- Student-entered activity is self-reported, not official institutional data.
- A published URL alone does not prove current service health; the live smoke checks above remain outstanding.


## Product direction update — 2026-11-25

- Email verification is intentionally not part of the product. Registration remains direct and does not require Resend configuration.
- Removed the experimental email-verification API, database model, UI page, tests, and deployment instructions.
- Refreshed the visual system with clearer surface hierarchy, refined dark/light palettes, responsive spacing, stronger focus states, hover feedback, and reduced-motion support.
- Theme selection now respects the operating-system preference on first visit, persists the user's explicit choice, and exposes an accessible toggle label.
- The same theme switch remains available on public pages and authenticated workspaces.
- Remaining release work: verify the Vercel deployment, test the public landing/auth flows on mobile and desktop, and run role-based smoke tests against the deployed backend.


## Dashboard reliability update — 2026-11-25

- Dashboard loading now exposes an accessible status state.
- A failed dashboard request displays an actionable error and retry control rather than leaving the user on an indefinite spinner.
- The core dashboard is no longer blocked when optional trend or subject analytics requests fail independently.
- Empty chart states explain how additional assessments unlock insights.
- Zero-valued scores and attendance are rendered as valid values rather than missing data.
- Prediction history includes a clear empty state.
- These dashboard reliability improvements are submitted in PR #11 and are pending CI review/merge.


## Study planner UX update — 2026-11-25

- Added interactive completion checkboxes for each generated weekly study activity.
- Added overall weekly completion percentage and completed/total activity counts.
- Added per-day completion counts and clearer subject/task grouping.
- Completion is intentionally session-scoped for now; it resets when a new plan is generated or the page session is restarted. Persistent server-side task completion is a future enhancement and is not claimed as implemented.
- This update is submitted in PR #12 and requires CI and production verification.
