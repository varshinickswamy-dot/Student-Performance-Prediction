from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


class ExamPrepRequest(BaseModel):
    subject: str = Field(min_length=2, max_length=100)
    exam_date: date
    hours_per_day: float = Field(default=2.0, ge=0.5, le=12)
    topics: list[str] = Field(min_length=1, max_length=20)


class QuestionGeneratorRequest(BaseModel):
    subject: str = Field(min_length=2, max_length=100)
    topic: str = Field(min_length=2, max_length=120)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    count: int = Field(default=5, ge=1, le=10)


class CareerReadinessRequest(BaseModel):
    target_role: Literal["Software Developer", "Data Analyst", "AI/ML Engineer", "Cybersecurity Analyst", "Cloud Engineer"]
    skills: list[str] = Field(default_factory=list, max_length=40)
    projects_count: int = Field(default=0, ge=0, le=100)
    internship_experience: bool = False
    portfolio_ready: bool = False


class ScholarshipScreenRequest(BaseModel):
    academic_percentage: float = Field(ge=0, le=100)
    course_area: str = Field(min_length=2, max_length=100)
    annual_income_band: Literal["undisclosed", "lower", "middle", "higher"] = "undisclosed"
    state: str = Field(default="", max_length=80)
