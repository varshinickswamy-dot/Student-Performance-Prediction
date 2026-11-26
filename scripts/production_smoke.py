"""Read-only production smoke checks for the deployed EduPredict services.

Usage:
  python scripts/production_smoke.py

Optional environment variables:
  EDUPREDICT_FRONTEND_URL  Published Vercel origin
  EDUPREDICT_API_URL       Render API origin
"""
from __future__ import annotations

import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FRONTEND_URL = os.getenv(
    "EDUPREDICT_FRONTEND_URL",
    "https://student-performance-prediction-amber.vercel.app",
).rstrip("/")
API_URL = os.getenv(
    "EDUPREDICT_API_URL",
    "https://student-performance-backend-nujh.onrender.com",
).rstrip("/")


def request(label: str, url: str, *, method: str = "GET", headers: dict[str, str] | None = None) -> bool:
    req = Request(url, method=method, headers=headers or {})
    try:
        with urlopen(req, timeout=30) as response:
            ok = 200 <= response.status < 300
            print(f"[{'PASS' if ok else 'FAIL'}] {label}: HTTP {response.status}")
            return ok
    except HTTPError as exc:
        print(f"[FAIL] {label}: HTTP {exc.code}")
    except (URLError, TimeoutError) as exc:
        print(f"[FAIL] {label}: {exc}")
    return False


def main() -> int:
    results = [
        request("Frontend responds", FRONTEND_URL),
        request("Backend liveness", f"{API_URL}/api/health/live"),
        request("Backend readiness (database + model)", f"{API_URL}/api/health/ready"),
        request(
            "Frontend CORS preflight",
            f"{API_URL}/api/health",
            method="OPTIONS",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        ),
    ]
    print(f"\n{sum(results)}/{len(results)} production checks passed.")
    if not all(results):
        print("Review the failing service, Render logs, Vercel environment variables and CORS origins.")
        return 1
    print("Read-only smoke checks passed. Authenticated user journeys still require a manual test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
