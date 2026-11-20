from pydantic import BaseModel, Field


class FinalExamPredictionRequest(BaseModel):
    attendance_pct: float = Field(ge=0, le=100)
    study_hours_per_week: float = Field(ge=0, le=60)
    sleep_hours: float = Field(ge=0, le=24)
    previous_sgpa: float = Field(ge=0, le=10)
    backlogs: int = Field(ge=0, le=30)
    internal_test_1: float = Field(ge=0, le=50)
    internal_test_2: float = Field(ge=0, le=50)
    assignment_score: float = Field(ge=0, le=20)
    extracurricular: bool = False
    internet_access: bool = True
