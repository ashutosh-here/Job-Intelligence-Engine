from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_jobs: int
    jobs_today: int
    avg_semantic_score: float
    avg_final_score: float


class SalaryBucket(BaseModel):
    bucket: str
    count: int


class TrendPoint(BaseModel):
    date: str
    discovered_jobs: int
