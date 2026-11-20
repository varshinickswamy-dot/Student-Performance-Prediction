"""Deterministic, transparent academic planning helpers.

These features are decision-support utilities, not validated student-outcome
models. They never alter or retrain the deployed prediction artifact.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any


def digital_twin_snapshot(user: Any, predictions: list, goals: list, activities: list) -> dict:
    latest = predictions[0] if predictions else None
    previous = predictions[1] if len(predictions) > 1 else None
    completed = sum(1 for goal in goals if goal.status == "completed")
    total_goals = len(goals)
    study_hours = sum(
        float(item.value) for item in activities
        if item.activity_type == "study_session" and item.occurred_on >= date.today() - timedelta(days=30)
    )
    attendance_items = [
        item for item in activities
        if item.activity_type == "attendance" and item.occurred_on >= date.today() - timedelta(days=30)
    ]
    attendance_rate = (
        round(100 * sum(1 for item in attendance_items if float(item.value) >= 1) / len(attendance_items), 1)
        if attendance_items else None
    )
    timeline = [{
        "prediction_id": item.id,
        "date": item.created_at.date().isoformat(),
        "subject": item.subject,
        "model_estimate": float(item.predicted_score),
        "model_version": item.model_version,
    } for item in reversed(predictions[:12])]
    trend = None
    if latest and previous:
        trend = round(float(latest.predicted_score) - float(previous.predicted_score), 1)
    return {
        "student": {"name": user.full_name, "course": user.course, "department": user.department,
                    "semester": user.semester, "institution": user.institution_name},
        "status": "initialized" if latest else "insufficient_data",
        "latest_assessment": None if latest is None else {
            "prediction_id": latest.id, "subject": latest.subject, "semester": latest.semester,
            "model_estimate": float(latest.predicted_score), "performance_category": latest.performance_category,
            "model_version": latest.model_version, "inputs": latest.input_data,
        },
        "recent_estimate_change": trend,
        "goal_progress": {"completed": completed, "total": total_goals,
                          "completion_percentage": round(completed * 100 / total_goals, 1) if total_goals else None},
        "activity_last_30_days": {"study_hours": round(study_hours, 1),
                                  "attendance_entries": len(attendance_items),
                                  "recorded_attendance_percentage": attendance_rate},
        "timeline": timeline,
        "data_sources": ["your saved predictions", "your study goals", "your manually recorded activities"],
        "limitations": [
            "This is a descriptive snapshot, not a continuously learning or scientifically validated digital twin.",
            "Model estimates use the dataset and model version shown; synthetic demonstration data is not validated for real student outcomes.",
            "Activity summaries include only entries you have manually recorded.",
        ],
    }


def recovery_plan(predictions: list) -> dict:
    if not predictions:
        return {"status": "insufficient_data", "steps": [],
                "message": "Create an academic assessment first to generate a plan from your own saved inputs."}
    latest = predictions[0]
    data = latest.input_data or {}
    priorities = []
    checks = [
        ("attendance", float(data.get("attendance", 0)), 75,
         "Build an attendance recovery routine", "Review missed classes, identify attendance barriers and plan attendance for the next two weeks."),
        ("previous_marks", float(data.get("previous_marks", 0)), 60,
         "Rebuild prerequisite knowledge", "Choose two prerequisite topics, review class notes and complete short practice sets."),
        ("assignment_scores", float(data.get("assignment_scores", 0)), 60,
         "Recover assignment performance", "Review feedback, correct errors and ask your teacher about unclear requirements."),
        ("homework_completion", float(data.get("homework_completion", 0)), 65,
         "Improve task completion", "Break pending work into small tasks and schedule three focused completion blocks."),
        ("study_hours", float(data.get("study_hours", 0)), 3,
         "Establish a consistent study routine", "Begin with a realistic focused session and review progress at the end of each week."),
    ]
    for key, value, cutoff, title, action in checks:
        if value < cutoff:
            priorities.append({"area": key, "title": title, "action": action, "observed_value": value, "target_review_threshold": cutoff})
    if not priorities:
        priorities.append({"area": "maintenance", "title": "Maintain and consolidate progress",
                           "action": "Continue active recall, weekly revision and regular feedback; reassess after your next assessment.",
                           "observed_value": None, "target_review_threshold": None})
    return {
        "status": "generated", "based_on_prediction_id": latest.id,
        "model_version": latest.model_version, "subject": latest.subject,
        "weeks": [
            {"week": 1, "focus": "Stabilize", "tasks": priorities[:3]},
            {"week": 2, "focus": "Practise", "tasks": priorities[:3]},
            {"week": 3, "focus": "Apply", "tasks": priorities[:3]},
            {"week": 4, "focus": "Review", "tasks": priorities[:3]},
        ],
        "review_rule": "Review your own recorded activities and teacher feedback weekly; adjust the plan when circumstances change.",
        "disclaimer": "This is a practical planning checklist based on self-reported inputs, not a clinical assessment or a guarantee of score improvement.",
    }


def exam_preparation_plan(subject: str, exam_date: date, hours_per_day: float, topics: list[str]) -> dict:
    today = date.today()
    days_left = (exam_date - today).days
    if days_left < 0:
        raise ValueError("Exam date must be today or in the future.")
    clean_topics = [topic.strip()[:100] for topic in topics if topic.strip()][:20]
    if not clean_topics:
        raise ValueError("Add at least one topic.")
    total_days = max(1, days_left + 1)
    schedule = []
    for index in range(total_days):
        topic = clean_topics[index % len(clean_topics)]
        if total_days - index <= 2:
            mode = "Revision and active recall"
            task = f"Revise {topic}, summarize key points and review mistakes."
        elif index % 4 == 3:
            mode = "Practice and self-check"
            task = f"Complete a timed practice set for {topic} and review incorrect answers."
        else:
            mode = "Concept learning"
            task = f"Study {topic}, make concise notes and explain the concept in your own words."
        schedule.append({"date": (today + timedelta(days=index)).isoformat(),
                         "day": index + 1, "topic": topic, "mode": mode,
                         "task": task, "planned_hours": round(hours_per_day, 1)})
    return {"subject": subject.strip(), "exam_date": exam_date.isoformat(),
            "days_until_exam": days_left, "daily_hours": round(hours_per_day, 1),
            "schedule": schedule,
            "disclaimer": "This is a suggested schedule based on the topics and time you entered. It does not predict exam questions or guarantee results."}


def practice_questions(subject: str, topic: str, difficulty: str, count: int) -> dict:
    templates = {
        "easy": [
            ("Recall", "Define {topic} in your own words and give one example."),
            ("Understanding", "Explain the purpose of {topic} and identify its main components."),
            ("Compare", "List two important characteristics of {topic}."),
            ("Application", "Describe a simple situation in {subject} where {topic} is useful."),
        ],
        "medium": [
            ("Application", "Apply {topic} to solve a practical problem from {subject}; show your reasoning."),
            ("Analysis", "Break {topic} into its major steps or components and explain how they interact."),
            ("Comparison", "Compare two approaches related to {topic}; state when each is appropriate."),
            ("Debugging", "A solution involving {topic} gives an unexpected result. Describe a systematic way to investigate it."),
        ],
        "hard": [
            ("Evaluation", "Critically evaluate the assumptions and limitations of a method based on {topic}."),
            ("Design", "Design a solution for a realistic {subject} problem using {topic}; justify your choices."),
            ("Synthesis", "Combine {topic} with a related concept to solve a multi-step problem and explain trade-offs."),
            ("Research", "Propose an experiment to compare two approaches to {topic}; define variables and evaluation criteria."),
        ],
    }
    bank = templates[difficulty]
    questions = []
    for index in range(count):
        kind, template = bank[index % len(bank)]
        questions.append({"number": index + 1, "type": kind,
                          "question": template.format(topic=topic.strip(), subject=subject.strip()),
                          "self_check": "Check conceptual accuracy, reasoning, worked steps and whether the response addresses the prompt."})
    return {"subject": subject.strip(), "topic": topic.strip(), "difficulty": difficulty,
            "questions": questions,
            "notice": "These are generated practice prompts, not questions from a real or leaked examination. No answer key is supplied where a topic-specific factual answer cannot be verified."}


ROLE_SKILLS = {
    "software developer": {"python", "java", "javascript", "react", "sql", "git", "apis", "testing"},
    "data analyst": {"python", "sql", "excel", "statistics", "data visualization", "power bi", "communication"},
    "ai/ml engineer": {"python", "machine learning", "statistics", "pandas", "numpy", "scikit-learn", "deep learning"},
    "cybersecurity analyst": {"networking", "linux", "security fundamentals", "python", "incident response", "siem"},
    "cloud engineer": {"linux", "networking", "docker", "cloud fundamentals", "ci/cd", "python"},
}


def career_readiness(payload: Any) -> dict:
    role = payload.target_role.casefold()
    required = ROLE_SKILLS[role]
    supplied = {skill.strip().casefold() for skill in payload.skills}
    matched = sorted(required & supplied)
    missing = sorted(required - supplied)
    coverage = round(len(matched) * 100 / len(required), 1)
    evidence = []
    if payload.projects_count:
        evidence.append(f"{payload.projects_count} project(s) self-reported")
    if payload.internship_experience:
        evidence.append("Internship experience self-reported")
    if payload.portfolio_ready:
        evidence.append("Portfolio marked ready by the student")
    return {
        "target_role": payload.target_role, "skill_coverage_percentage": coverage,
        "matched_skills": matched, "suggested_skill_gaps": missing,
        "experience_evidence": evidence,
        "next_steps": [f"Build a small portfolio project demonstrating {skill}." for skill in missing[:4]],
        "interpretation": "This is a transparent checklist match against a small illustrative skill map, not a hiring probability, job guarantee or validated employability score.",
    }


def scholarship_pathways(payload: Any) -> dict:
    matches = []
    area = payload.course_area.casefold()
    if payload.academic_percentage >= 75:
        matches.append({"pathway": "Merit-based scholarships", "match": "potential",
                        "reason": "Your self-reported academic percentage meets this platform's exploratory 75% screening threshold.",
                        "verify": "Check the current minimum marks, institution and course rules on the official scholarship notice."})
    if payload.annual_income_band in {"lower", "middle"}:
        matches.append({"pathway": "Need-based financial assistance", "match": "potential",
                        "reason": "You selected an income band that may be relevant to means-tested support.",
                        "verify": "Check the official income certificate, family income ceiling and documentation requirements."})
    if any(term in area for term in ("engineering", "technology", "computer", "science", "ai", "data")):
        matches.append({"pathway": "STEM and technical education support", "match": "potential",
                        "reason": "Your selected course area is related to STEM or technology.",
                        "verify": "Confirm whether the scheme supports your exact course, institution and year of study."})
    if payload.state.strip():
        matches.append({"pathway": "State and domicile-based schemes", "match": "explore",
                        "reason": f"You entered {payload.state.strip()} as your state.",
                        "verify": "Check the relevant state government's official scholarship portal and current domicile rules."})
    matches.append({"pathway": "Institutional fee waivers and alumni funds", "match": "explore",
                    "reason": "Many institutions publish their own aid and fee-concession criteria.",
                    "verify": "Contact your institution's scholarship or student welfare office."})
    return {
        "screening_inputs": {"academic_percentage": payload.academic_percentage,
                             "course_area": payload.course_area, "annual_income_band": payload.annual_income_band,
                             "state": payload.state},
        "potential_pathways": matches,
        "next_steps": ["Verify current dates and eligibility on the official scheme notice.",
                       "Prepare marksheets, identity, bank and income/domicile documents only when required by the official application.",
                       "Never pay an agent to obtain a scholarship; use official application channels."],
        "disclaimer": "This is an exploratory pathway matcher, not a list of verified live awards or a determination of eligibility. Thresholds are screening hints only; official scheme rules always control.",
    }
