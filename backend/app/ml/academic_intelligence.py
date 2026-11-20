"""Transparent, rule-based academic support signals and study planning.

These heuristics are decision-support prompts, not validated probabilities or
high-stakes student classifications. They only use the authenticated student's
own saved prediction inputs.
"""
from __future__ import annotations

from datetime import date, timedelta


def build_academic_risk_assessment(predictions: list) -> dict:
    if not predictions:
        return {
            "status": "insufficient_data",
            "risk_level": None,
            "risk_points": None,
            "factors": [],
            "actions": ["Create an academic assessment to receive personalized support insights."],
            "disclaimer": "This is a transparent rule-based support screen, not a validated probability or diagnosis.",
        }

    latest = predictions[0]
    data = latest.input_data or {}
    factors: list[dict] = []
    points = 0

    checks = [
        ("attendance", float(data.get("attendance", 0)), 60, 75,
         "Attendance is below 60%.", "Attendance is below 75%.",
         "Review attendance barriers and agree on a realistic weekly attendance target."),
        ("previous_marks", float(data.get("previous_marks", 0)), 45, 60,
         "Previous marks are below 45%.", "Previous marks are below 60%.",
         "Revisit prerequisite concepts and schedule short, topic-focused practice."),
        ("study_hours", float(data.get("study_hours", 0)), 1.5, 3,
         "Reported study time is below 1.5 hours per day.", "Reported study time is below 3 hours per day.",
         "Start with a manageable daily focused-study block and increase gradually."),
        ("assignment_scores", float(data.get("assignment_scores", 0)), 40, 60,
         "Assignment scores are below 40%.", "Assignment scores are below 60%.",
         "Review assignment feedback and practise the question types causing difficulty."),
    ]
    for key, value, high_cutoff, moderate_cutoff, high_message, moderate_message, action in checks:
        if value < high_cutoff:
            points += 2
            factors.append({"factor": key, "severity": "high", "observation": high_message, "suggested_action": action})
        elif value < moderate_cutoff:
            points += 1
            factors.append({"factor": key, "severity": "moderate", "observation": moderate_message, "suggested_action": action})

    trend = None
    if len(predictions) >= 2:
        trend = round(float(predictions[0].predicted_score) - float(predictions[1].predicted_score), 1)
        if trend <= -10:
            points += 2
            factors.append({
                "factor": "recent_prediction_trend", "severity": "high",
                "observation": f"The latest model estimate is {abs(trend):.1f} points below the previous estimate.",
                "suggested_action": "Review what changed since the previous assessment and seek subject-specific support.",
            })
        elif trend <= -5:
            points += 1
            factors.append({
                "factor": "recent_prediction_trend", "severity": "moderate",
                "observation": f"The latest model estimate is {abs(trend):.1f} points below the previous estimate.",
                "suggested_action": "Monitor the next assessment and revisit the current study routine.",
            })

    level = "high" if points >= 4 else "moderate" if points >= 2 else "low"
    actions = [item["suggested_action"] for item in factors]
    if not actions:
        actions = ["Maintain a sustainable routine and review progress after the next assessment."]
    return {
        "status": "assessed",
        "risk_level": level,
        "risk_points": points,
        "risk_scale": "Rule-based support points; not a probability or validated risk score",
        "subject": latest.subject,
        "semester": latest.semester,
        "latest_prediction_id": latest.id,
        "latest_model_estimate": float(latest.predicted_score),
        "recent_estimate_change": trend,
        "factors": factors,
        "actions": actions,
        "disclaimer": "This transparent heuristic highlights inputs that may warrant support. It is not a validated prediction of failure, diagnosis, or basis for punitive decisions.",
    }


def build_weekly_study_plan(
    prediction,
    available_hours_per_day: float = 2.0,
    focus_subject: str | None = None,
) -> dict:
    data = prediction.input_data or {}
    subject = (focus_subject or prediction.subject or "Your subject").strip()[:100]
    hours = max(0.5, min(float(available_hours_per_day), 8.0))
    tasks: list[dict] = []

    if float(data.get("previous_marks", 0)) < 60:
        priorities = ["Review prerequisite concepts", "Practise 10 foundational questions", "Make a one-page concept summary"]
    elif float(data.get("assignment_scores", 0)) < 65:
        priorities = ["Review assignment feedback", "Solve a similar practice set", "Correct and document recurring errors"]
    else:
        priorities = ["Revise the latest topic", "Complete a timed practice set", "Summarize key concepts from memory"]

    if float(data.get("attendance", 0)) < 75:
        priorities[0] = "Catch up on missed class notes and identify unclear topics"
    if float(data.get("study_hours", 0)) < 3:
        priorities[1] = "Complete one focused study session without distractions"

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    activities = [
        [priorities[0], "Write down three questions to clarify"],
        [priorities[1], "Check answers and note mistakes"],
        ["Revise the weakest concept", "Use active recall for 15 minutes"],
        [priorities[2], "Practise questions from an earlier topic"],
        ["Complete a short self-test", "Review incorrect answers"],
        ["Connect concepts across the unit", "Update your progress notes"],
        ["Weekly recap and self-review", "Plan the next week's focus"],
    ]
    for index, day in enumerate(days):
        tasks.append({
            "day": day,
            "date": (date.today() + timedelta(days=index)).isoformat(),
            "subject": subject,
            "estimated_hours": round(hours, 1),
            "activities": activities[index],
            "completion_guidance": "Mark this session complete in your own study tracker after finishing it.",
        })
    return {
        "subject": subject,
        "available_hours_per_day": round(hours, 1),
        "based_on_prediction_id": prediction.id,
        "model_version": prediction.model_version,
        "days": tasks,
        "disclaimer": "This is a suggested study schedule based on the latest saved inputs, not a guarantee of academic results.",
    }


def build_student_notifications(predictions: list, goals: list) -> list[dict]:
    notifications: list[dict] = []
    risk = build_academic_risk_assessment(predictions)
    if risk["status"] == "assessed" and risk["risk_level"] in {"high", "moderate"}:
        notifications.append({
            "id": "academic-support",
            "type": "academic_support",
            "severity": risk["risk_level"],
            "title": "Academic support areas identified",
            "message": f"{len(risk['factors'])} input area(s) may benefit from attention. Review your academic support assessment.",
            "action": "/risk",
        })
    for goal in goals:
        if goal.status != "completed" and goal.target_date:
            remaining = (goal.target_date - date.today()).days
            if remaining < 0:
                notifications.append({
                    "id": f"goal-overdue-{goal.id}", "type": "goal",
                    "severity": "moderate", "title": "Study goal is past its target date",
                    "message": goal.title, "action": "/goals",
                })
            elif remaining <= 3:
                notifications.append({
                    "id": f"goal-due-{goal.id}", "type": "goal",
                    "severity": "info", "title": "Study goal due soon",
                    "message": f"{goal.title} · {remaining} day(s) remaining",
                    "action": "/goals",
                })
    return notifications
