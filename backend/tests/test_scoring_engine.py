from datetime import datetime, timedelta, timezone

from app.scoring.engine import ScoringEngine


def test_scoring_formula_generates_normalized_final_score() -> None:
    engine = ScoringEngine()
    posted_date = datetime.now(timezone.utc) - timedelta(days=2)

    breakdown = engine.compute(
        semantic_score=0.9,
        salary_min=120000,
        salary_max=160000,
        funding_stage="Series C",
        company_size="500-1000",
        posted_date=posted_date,
        remote_flag=True,
    )

    assert 0.0 <= breakdown.final_score <= 1.0
    assert breakdown.semantic_score == 0.9
    assert breakdown.salary_score >= 0.65
    assert breakdown.remote_bonus == 1.0
