from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import Settings, get_settings


@dataclass
class ScoreBreakdown:
    semantic_score: float
    salary_score: float
    company_stability: float
    recency: float
    remote_bonus: float
    final_score: float


class ScoringEngine:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def salary_score(self, salary_min: int | None, salary_max: int | None) -> float:
        if salary_min is None and salary_max is None:
            return 0.2
        midpoint = (
            (salary_min + salary_max) / 2
            if salary_min is not None and salary_max is not None
            else salary_min or salary_max or 0
        )
        # Score curves around common software salary bands.
        if midpoint >= 200000:
            return 1.0
        if midpoint >= 150000:
            return 0.85
        if midpoint >= 100000:
            return 0.65
        if midpoint >= 70000:
            return 0.45
        return 0.2

    def company_stability(self, funding_stage: str | None, company_size: str | None) -> float:
        funding_map = {
            "public": 1.0,
            "series d": 0.8,
            "series c": 0.72,
            "series b": 0.65,
            "series a": 0.55,
            "seed": 0.42,
            "bootstrapped": 0.6,
        }
        size_map = {
            "enterprise": 0.9,
            "1000+": 0.85,
            "500-1000": 0.75,
            "200-500": 0.65,
            "50-200": 0.55,
            "1-50": 0.35,
        }
        funding = funding_map.get((funding_stage or "").lower(), 0.5)
        size = size_map.get((company_size or "").lower(), 0.5)
        return round((funding + size) / 2, 4)

    def recency_score(self, posted_date: datetime | None) -> float:
        if posted_date is None:
            return 0.3
        now = datetime.now(timezone.utc)
        normalized = (
            posted_date.replace(tzinfo=timezone.utc)
            if posted_date.tzinfo is None
            else posted_date.astimezone(timezone.utc)
        )
        delta_days = (now - normalized).days
        if delta_days <= 1:
            return 1.0
        if delta_days <= 3:
            return 0.85
        if delta_days <= 7:
            return 0.65
        if delta_days <= 14:
            return 0.45
        return 0.2

    def compute(
        self,
        semantic_score: float,
        salary_min: int | None,
        salary_max: int | None,
        funding_stage: str | None,
        company_size: str | None,
        posted_date: datetime | None,
        remote_flag: bool,
    ) -> ScoreBreakdown:
        salary = self.salary_score(salary_min, salary_max)
        stability = self.company_stability(funding_stage, company_size)
        recency = self.recency_score(posted_date)
        remote_bonus = 1.0 if remote_flag else 0.0

        final_score = (
            self.settings.score_weight_semantic * semantic_score
            + self.settings.score_weight_salary * salary
            + self.settings.score_weight_company_stability * stability
            + self.settings.score_weight_recency * recency
            + self.settings.score_weight_remote_bonus * remote_bonus
        )

        return ScoreBreakdown(
            semantic_score=round(semantic_score, 4),
            salary_score=round(salary, 4),
            company_stability=round(stability, 4),
            recency=round(recency, 4),
            remote_bonus=round(remote_bonus, 4),
            final_score=round(final_score, 4),
        )
