from pydantic import BaseModel, field_validator
from typing import Optional

class JobExtraction(BaseModel):
    posting_id: int
    seniority: str
    seniority_confidence: float
    skills: list[str]
    skills_by_category: dict

    @field_validator("seniority")
    @classmethod
    def seniority_must_be_valid(cls, value):
        allowed = ["junior", "mid-level", "senior", "unknown"]
        if value not in allowed:
            raise ValueError(f"seniority must be one of {allowed}, got '{value}'")
        return value

    @field_validator("seniority_confidence")
    @classmethod
    def confidence_must_be_between_0_and_1(cls, value):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"confidence must be between 0 and 1, got {value}")
        return value

    @field_validator("skills")
    @classmethod
    def skills_must_be_list(cls, value):
        if not isinstance(value, list):
            raise ValueError("skills must be a list")
        return value