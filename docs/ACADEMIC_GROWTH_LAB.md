# EduPredict Academic Growth Lab

## Student API features

All routes below require a valid student bearer token. They use the authenticated account only.

| Method and route | Purpose | Persistence |
|---|---|---|
| GET `/api/student/digital-twin` | Descriptive snapshot of profile, saved prediction timeline, goals and manually logged activity | Read-only |
| GET `/api/student/recovery-plan` | Four-week checklist derived from the latest saved prediction inputs | Read-only |
| POST `/api/student/exam-preparation` | Build a date-by-date plan from a subject, future exam date, available hours and topics | Not persisted |
| POST `/api/student/question-generator` | Create generic topic-based practice prompts at easy, medium or hard level | Not persisted |
| POST `/api/student/career-readiness` | Compare self-reported skills with an illustrative skill map for five entry-level role families | Not persisted |
| POST `/api/student/scholarship-matches` | Screen broad scholarship pathways using self-reported marks, course area, optional income band and state | Not persisted |

### Example exam-preparation request

```json
{
  "subject": "Database Management Systems",
  "exam_date": "2026-12-05",
  "hours_per_day": 2,
  "topics": ["Normalization", "SQL joins", "Transactions"]
}
```

The exam date must be today or later and within 90 days. Hours per day must be between 0.5 and 12. The topic list accepts 1–20 entries.

### Example practice-question request

```json
{
  "subject": "Computer Science",
  "topic": "Database normalization",
  "difficulty": "medium",
  "count": 5
}
```

Question prompts are structured practice frameworks. They are not sourced from a real examination, and no unverified answer key is fabricated.

### Career readiness request

The supported target roles are Software Developer, Data Analyst, AI/ML Engineer, Cybersecurity Analyst and Cloud Engineer. Students enter skills as a list and self-report project count, internship experience and portfolio readiness. The returned coverage percentage is the fraction of role-map skills the student entered; it is not a hiring or employability probability.

### Scholarship pathway screening

The matcher returns broad categories (merit, need-based, STEM/technical, state/domicile and institutional aid) and verification reminders. It does not query a live scholarship database, guarantee eligibility, or represent an award as currently open. Applicants must verify current scheme notices and deadlines with official providers.

## Staff intelligence

| Method and route | Authorization | Scope |
|---|---|---|
| GET `/api/teacher/intelligence` | Teacher role | Only students assigned to the authenticated teacher |
| GET `/api/institution/intelligence` | Institution administrator role | Aggregate records matching the authenticated institution |

The teacher endpoint includes assigned-student names and support indicators to support authorized teaching workflows. The institution endpoint does not return individual student records. Department and semester groups with fewer than five students are suppressed.

## Existing functionality reused

- The What-if Simulator continues to call `POST /api/predictions/simulate` and uses the same deployed model pipeline without saving scenarios.
- Existing risk assessment remains a transparent rule-based support screen, not a calibrated probability.
- Existing explanation endpoints continue to return model-specific Ridge coefficient contributions, not SHAP values or causal effects.
- Existing seven-day study planner remains available separately from the exam planner.
- Existing teacher assignment isolation and institution role checks remain in place.

## Deployment compatibility

No new Python package, database table, database migration, secret, or external provider is required. The additions are API routes and deterministic service functions that use the existing FastAPI app, authentication, SQLAlchemy models and Render environment. The Vercel page calls the existing configured API client, so the current Render API base URL remains unchanged.

After merging this branch, the GitHub push alone does not update Render. Confirm the Render service deploys the merged commit, then verify:

- `GET /api/health`
- `GET /api/health/ready`
- `GET /docs` and confirm the new routes appear
- Student-only endpoints return 401 without a token and 403 for non-student roles
- Teacher and institution endpoints enforce their respective roles

The frontend deployment should rebuild from the updated default branch. No new Vercel or Render environment variables are required.

## Responsible-use limitations

The deployed Ridge model is trained on seeded synthetic demonstration data. These additions do not improve or validate its real-world predictive performance. Digital Twin is a descriptive snapshot, not a continuously learning simulation. Recovery and exam schedules are suggestions. Career and scholarship matching are exploratory decision-support tools. Do not use any of these outputs as the sole basis for admission, grading, discipline, hiring, financial aid or other high-impact decisions.
