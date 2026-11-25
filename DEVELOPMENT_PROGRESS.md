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

1. Verify Render production environment variables and startup: `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FRONTEND_URL`, and `ENVIRONMENT=production`.
2. Confirm the Render PostgreSQL database is persistent and existing records remain intact.
3. Run live smoke tests for `/api/health/ready`, registration, login, prediction, history, and CORS from the published Vercel site. These checks are not yet confirmed.
4. Confirm Vercel has `VITE_API_BASE_URL=https://student-performance-backend-nujh.onrender.com`; the latest GitHub commit reports a successful Vercel deployment status, but browser-level production flows still need verification.
5. Configure password-reset email delivery only if that feature is required; otherwise retain the honest unavailable response.
6. Supply an authorised, documented real student dataset before attempting real-world model evaluation. The current model is synthetic demonstration data only.
7. Keep the final-exam candidate optional unless its artifact is securely hosted and reviewed. Do not commit private CSVs or Joblib artifacts.
8. Re-check GitHub Actions backend tests and frontend build for the latest main commit before declaring release complete.
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
- These dashboard reliability improvements were merged through PR #11 after CI passed.


## Study planner UX update — 2026-11-25

- Added interactive completion checkboxes for each generated weekly study activity.
- Added overall weekly completion percentage and completed/total activity counts.
- Added per-day completion counts and clearer subject/task grouping.
- Completion is intentionally session-scoped for now; it resets when a new plan is generated or the page session is restarted. Persistent server-side task completion is a future enhancement and is not claimed as implemented.
- This update was merged through PR #12 after CI passed. Production verification remains outstanding.


## Academic analytics UX update — 2026-11-25

- Added summary metrics for saved assessments, average model estimate, latest model estimate, and tracked subjects.
- Replaced the study-hours bar chart with a scatter plot to communicate the relationship as a descriptive comparison rather than implying categories.
- Added date-based saved model-estimate trend visualization and clearer chart explanations.
- Analytics requests now load independently; partial endpoint failures no longer blank the entire page.
- Added loading, retry, and empty states.
- Added an explicit responsible-use note: charts represent model-generated estimates, not verified academic results or causal evidence.
- Uses existing analytics API routes; no backend schema or endpoint changes.
- Pending CI and merge in PR #13; production deployment remains to be verified.


## Latest repository verification — 2026-11-25

- PR #13 academic analytics improvements are merged into `main` (commit `49c5b75`).
- PR #14 adds PostgreSQL stale-connection validation and recycling (commit `e4c7bd4`).
- PR #15 adds clean recovery from expired authentication sessions (commit `6b2fd82`). Protected API 401 responses clear stored sessions and the app redirects the user to login.
- The latest main commit reports a successful Vercel deployment status in GitHub.
- The frontend API client defaults to the deployed Render backend in production and uses `VITE_API_BASE_URL` when configured.
- Live Render readiness and authenticated end-to-end smoke tests could not be confirmed during this review. Do not mark production fully verified until those checks pass.
