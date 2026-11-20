# Android Integration Guide

## Repository audit result

The current repository contains the React/Vite web client and FastAPI backend, but no Android Gradle project or Kotlin source files. Do not copy over or repurpose a different Android Studio project. Create or select a dedicated EduPredict Android project in Android Studio, then use this guide to connect it to the existing backend.

## Production API

Use the existing HTTPS backend:

`https://student-performance-backend-nujh.onrender.com`

Do not create a second ML service or database in Android. The app should call the same FastAPI API used by the Vercel web client.

## Core API workflows

- Register: `POST /api/auth/register`
- Login: `POST /api/auth/login`
- Current account: `GET /api/auth/me`
- Student dashboard: `GET /api/student/dashboard`
- Create prediction: `POST /api/predictions/predict`
- Prediction history: `GET /api/predictions/history`
- Prediction explanation: `GET /api/predictions/{prediction_id}/explanation`
- What-if comparison: `POST /api/predictions/simulate`
- Academic support assessment: `GET /api/student/risk-assessment`
- Weekly study plan: `POST /api/student/study-plan`
- Study goals: `GET/POST /api/student/goals`, `PATCH/DELETE /api/student/goals/{goal_id}`
- Assistant: `POST /api/assistant/chat`
- Notifications: `GET /api/student/notifications`
- Readiness: `GET /api/health/ready`

Authenticated requests must send `Authorization: Bearer <access_token>`. Use HTTPS only. Never hardcode tokens, passwords, database URLs or provider API keys in the Android source.

## Suggested Android architecture

- Kotlin + Jetpack Compose for UI.
- Navigation Compose for routes.
- Retrofit + OkHttp for typed API requests.
- Kotlin serialization or Moshi for JSON.
- DataStore for non-sensitive preferences.
- Android Keystore-backed encrypted storage for access tokens; do not store credentials in plain SharedPreferences.
- ViewModel + StateFlow for screen state and lifecycle-aware collection.
- Repository layer to isolate network and local state.

## Minimum screen sequence

1. Login and registration.
2. Student dashboard.
3. Prediction form and prediction result.
4. Explanation and report view/share.
5. What-if simulator.
6. Academic risk assessment.
7. Weekly study planner and goals.
8. Assistant chat.
9. Notifications, prediction history and profile.
10. Settings and theme.

## Reliability requirements

- Show loading, offline, empty, unauthorized and server-error states.
- Handle Render cold starts with a visible retry state and reasonable network timeouts.
- On HTTP 401, clear the expired session and return to login.
- Do not retry non-idempotent prediction creation automatically without user confirmation.
- Use Android's document/share intents for PDF reports; verify the PDF bytes before exposing a share URI through FileProvider.
- Keep the UI usable on small screens and with large system font settings.
- Do not treat a successful health endpoint as proof that a user is authenticated.

## Model and data limitations

The deployed model currently identifies itself as `demo-ridge-v1` and uses a seeded synthetic demonstration dataset. Android must display the same limitation text as the web app. Do not claim validated real-world prediction accuracy or make high-stakes student decisions based on the demo model.

## Build and release checklist

- Configure the production base URL in a build configuration, not in a secret.
- Keep debug and production API hosts separate.
- Test login, refresh/re-entry, prediction, explanation, simulation, goals, assistant fallback, PDF sharing and logout on a physical Android device.
- Verify that no local development URL is present in the release APK.
- Sign release builds securely and never commit signing keys or passwords.
