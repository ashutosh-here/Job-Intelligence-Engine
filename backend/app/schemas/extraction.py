from datetime import datetime

from pydantic import BaseModel, Field


class ExtractedJob(BaseModel):
    job_title: str
    company_name: str
    location: str | None = None
    remote_flag: bool = False
    salary_min: int | None = None
    salary_max: int | None = None
    job_description: str
    required_skills: list[str] = Field(default_factory=list)
    seniority_level: str | None = None
    employment_type: str | None = None
    posted_date: datetime | None = None
    apply_link: str | None = None
    source_url: str
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
