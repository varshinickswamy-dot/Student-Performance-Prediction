from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str
    student_id: str | None = None
    institution_name: str | None = None
    department: str | None = None
    course: str | None = None
    semester: str | None = None
    academic_year: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: str
    role: str
    active: bool
    student_id: str | None = None
    institution_name: str | None = None
    department: str | None = None
    course: str | None = None
    semester: str | None = None
    academic_year: str | None = None
    created_at: datetime


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    student_id: str | None = None
    institution_name: str | None = None
    department: str | None = None
    course: str | None = None
    semester: str | None = None
    academic_year: str | None = None


class PredictionInput(BaseModel):
    subject: str = Field(min_length=2, max_length=100)
    semester: str = Field(min_length=1, max_length=50)
    study_hours: float = Field(ge=0, le=16)
    previous_marks: float = Field(ge=0, le=100)
    attendance: float = Field(ge=0, le=100)
    assignment_scores: float = Field(ge=0, le=100)
    class_participation: float = Field(ge=0, le=100)
    homework_completion: float = Field(ge=0, le=100)
    sleep_hours: float = Field(ge=0, le=16)
    extracurricular: bool = False
    internet_access: bool = True
    family_support: bool = True


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject: str
    semester: str
    predicted_score: float
    performance_category: str
    input_data: dict[str, Any]
    recommendations: list[dict[str, Any]]
    model_version: str
    created_at: datetime
