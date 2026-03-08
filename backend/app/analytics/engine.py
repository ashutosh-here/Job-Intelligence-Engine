from sqlalchemy import text
from sqlalchemy.orm import Session


class AnalyticsEngine:
    def overview(self, db: Session, user_id: int | None = None) -> dict:
        where = ""
        params: dict[str, int] = {}
        if user_id is not None:
            where = "WHERE EXISTS (SELECT 1 FROM sources s WHERE s.id = jobs.source_id AND s.user_id = :user_id)"
            params["user_id"] = user_id
        overview_stmt = text(
            """
            SELECT
                COUNT(*) AS total_jobs,
                COUNT(*) FILTER (
                    WHERE first_seen::date = NOW()::date
                ) AS jobs_today,
                COALESCE(AVG(semantic_score), 0) AS avg_semantic_score,
                COALESCE(AVG(final_score), 0) AS avg_final_score
            FROM jobs
            """
            + where
        )
        row = db.execute(overview_stmt, params).mappings().first()
        return {
            "total_jobs": int(row["total_jobs"]) if row else 0,
            "jobs_today": int(row["jobs_today"]) if row else 0,
            "avg_semantic_score": float(row["avg_semantic_score"]) if row else 0.0,
            "avg_final_score": float(row["avg_final_score"]) if row else 0.0,
        }

    def trends(self, db: Session, days: int = 30, user_id: int | None = None) -> dict:
        params: dict[str, int] = {"days": days}
        posting_where = "WHERE first_seen >= NOW() - (:days || ' days')::interval"
        if user_id is not None:
            posting_where += " AND EXISTS (SELECT 1 FROM sources s WHERE s.id = jobs.source_id AND s.user_id = :user_id)"
            params["user_id"] = user_id

        posting_stmt = text(
            """
            SELECT
                TO_CHAR(first_seen::date, 'YYYY-MM-DD') AS date,
                COUNT(*) AS discovered_jobs
            FROM jobs
            """
            + posting_where
            + """
            GROUP BY first_seen::date
            ORDER BY first_seen::date
            """
        )
        salary_where = ""
        if user_id is not None:
            salary_where = "WHERE EXISTS (SELECT 1 FROM sources s WHERE s.id = jobs.source_id AND s.user_id = :user_id)"
        salary_distribution_stmt = text(
            """
            SELECT
                CASE
                    WHEN salary_max IS NULL THEN 'unknown'
                    WHEN salary_max < 70000 THEN '<70k'
                    WHEN salary_max < 100000 THEN '70k-100k'
                    WHEN salary_max < 150000 THEN '100k-150k'
                    ELSE '150k+'
                END AS bucket,
                COUNT(*) AS count
            FROM jobs
            """
            + salary_where
            + """
            GROUP BY bucket
            ORDER BY count DESC
            """
        )
        semantic_where = ""
        if user_id is not None:
            semantic_where = "WHERE EXISTS (SELECT 1 FROM sources s WHERE s.id = jobs.source_id AND s.user_id = :user_id)"
        semantic_distribution_stmt = text(
            """
            SELECT
                CASE
                    WHEN semantic_score < 0.3 THEN 'low'
                    WHEN semantic_score < 0.7 THEN 'medium'
                    ELSE 'high'
                END AS bucket,
                COUNT(*) AS count
            FROM jobs
            """
            + semantic_where
            + """
            GROUP BY bucket
            ORDER BY bucket
            """
        )

        return {
            "posting_trends": [dict(row) for row in db.execute(posting_stmt, params).mappings()],
            "salary_distribution": [
                dict(row) for row in db.execute(salary_distribution_stmt, params).mappings()
            ],
            "semantic_distribution": [
                dict(row) for row in db.execute(semantic_distribution_stmt, params).mappings()
            ],
        }
