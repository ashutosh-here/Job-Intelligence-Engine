from datetime import datetime

from pydantic import BaseModel


class JobRead(BaseModel):
    id: int
    source_id: int
    company_id: int | None
    title: str
    location: str | None
    remote_flag: bool
    salary_min: int | None
    salary_max: int | None
    description: str
    required_skills: list[str] | None
    seniority_level: str | None
    employment_type: str | None
    posted_date: datetime | None
    apply_link: str | None
    source_url: str | None
    extraction_confidence: float
    semantic_score: float
    final_score: float
    first_seen: datetime
    last_updated: datetime

    model_config = {"from_attributes": True}


class SimilarJobRead(BaseModel):
    job: JobRead
    similarity: float
