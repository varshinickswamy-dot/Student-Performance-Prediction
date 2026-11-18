def performance_category(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Average"
    return "Needs Improvement"


def build_recommendations(data: dict) -> list[dict]:
    recommendations = []
    if data["study_hours"] < 3:
        recommendations.append({
            "priority": "High",
            "area": "Study Time",
            "action": "Create a consistent schedule with at least 3 focused study hours per day.",
            "benefit": "May improve concept retention and exam readiness.",
            "status": "Pending",
        })
    if data["attendance"] < 75:
        recommendations.append({
            "priority": "High",
            "area": "Attendance",
            "action": "Set a weekly attendance target and discuss barriers with an academic advisor.",
            "benefit": "Consistent participation supports stronger concept understanding.",
            "status": "Pending",
        })
    if data["previous_marks"] < 65:
        recommendations.append({
            "priority": "High",
            "area": "Previous Marks",
            "action": "Use subject-specific revision with targeted practice on weak topics.",
            "benefit": "Reinforces foundational knowledge before advanced work.",
            "status": "Pending",
        })
    if data["assignment_scores"] < 70:
        recommendations.append({
            "priority": "Medium",
            "area": "Assignments",
            "action": "Complete a regular assignment practice routine and review feedback promptly.",
            "benefit": "Builds applied understanding and reduces recurring errors.",
            "status": "Pending",
        })
    if data["sleep_hours"] < 7 or data["sleep_hours"] > 9:
        recommendations.append({
            "priority": "Medium",
            "area": "Sleep",
            "action": "Maintain a regular sleep schedule close to 7–9 hours per night.",
            "benefit": "Supports concentration, memory, and sustained study.",
            "status": "Pending",
        })
    if not recommendations:
        recommendations.append({
            "priority": "Low",
            "area": "Sustainable Progress",
            "action": "Keep the current routine and review performance after each assessment.",
            "benefit": "Helps maintain strengths and detect early changes.",
            "status": "In Progress",
        })
    return recommendations
