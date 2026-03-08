from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment.engine import EnrichmentEngine
from app.extraction.engine import ExtractionEngine
from app.models.company import Company
from app.models.extraction_log import ExtractionLog
from app.models.job import Job
from app.models.source import Source
from app.observability.metrics import pipeline_failures_total, pipeline_jobs_extracted_total
from app.outreach.engine import OutreachEngine
from app.scoring.engine import ScoringEngine
from app.semantic.engine import SemanticEngine
from app.sources.engine import SourceEngine
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.fingerprint import build_job_fingerprint
from app.utils.logging import get_logger
from app.vector.engine import VectorEngine


@dataclass
class PipelineResult:
    source_id: int
    discovered_links: int = 0
    extracted_jobs: int = 0
    failed_links: int = 0
    errors: list[str] = field(default_factory=list)


class PipelineOrchestrator:
    def __init__(
        self,
        source_engine: SourceEngine,
        extraction_engine: ExtractionEngine,
        semantic_engine: SemanticEngine,
        vector_engine: VectorEngine,
        enrichment_engine: EnrichmentEngine,
        scoring_engine: ScoringEngine,
        outreach_engine: OutreachEngine,
    ) -> None:
        self.source_engine = source_engine
        self.extraction_engine = extraction_engine
        self.semantic_engine = semantic_engine
        self.vector_engine = vector_engine
        self.enrichment_engine = enrichment_engine
        self.scoring_engine = scoring_engine
        self.outreach_engine = outreach_engine
        self.logger = get_logger("orchestrator")
        self._breakers: dict[int, CircuitBreaker] = {}

    def _get_breaker(self, source_id: int) -> CircuitBreaker:
        if source_id not in self._breakers:
            self._breakers[source_id] = CircuitBreaker(_name=f"source-{source_id}")
        return self._breakers[source_id]

    def _upsert_company(self, db: Session, company_name: str, website: str | None) -> Company:
        stmt = select(Company).where(Company.name == company_name)
        company = db.execute(stmt).scalar_one_or_none()
        if not company:
            company = Company(name=company_name)
            db.add(company)
            db.flush()

        enrichment = self.enrichment_engine.enrich(website)
        company.domain = company.domain or enrichment.domain
        company.size = company.size or enrichment.size
        company.funding_stage = company.funding_stage or enrichment.funding_stage
        company.industry = company.industry or enrichment.industry
        company.linkedin_url = company.linkedin_url or enrichment.linkedin_url
        return company

    def _upsert_job(self, db: Session, source: Source, company: Company, payload: dict) -> Job:
        fingerprint = payload["ingest_fingerprint"]
        stmt = select(Job).where(
            Job.source_id == source.id,
            Job.ingest_fingerprint == fingerprint,
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            existing.title = payload["title"]
            existing.location = payload.get("location")
            existing.remote_flag = payload.get("remote_flag", False)
            existing.salary_min = payload.get("salary_min")
            existing.salary_max = payload.get("salary_max")
            existing.description = payload["description"]
            existing.required_skills = payload.get("required_skills")
            existing.seniority_level = payload.get("seniority_level")
            existing.employment_type = payload.get("employment_type")
            existing.posted_date = payload.get("posted_date")
            existing.source_url = payload.get("source_url")
            existing.extraction_confidence = payload.get("extraction_confidence", 0.0)
            existing.ingest_fingerprint = fingerprint
            existing.last_updated = datetime.now(timezone.utc)
            return existing

        job = Job(
            source_id=source.id,
            company_id=company.id,
            title=payload["title"],
            location=payload.get("location"),
            remote_flag=payload.get("remote_flag", False),
            salary_min=payload.get("salary_min"),
            salary_max=payload.get("salary_max"),
            description=payload["description"],
            required_skills=payload.get("required_skills"),
            seniority_level=payload.get("seniority_level"),
            employment_type=payload.get("employment_type"),
            apply_link=payload.get("apply_link"),
            ingest_fingerprint=fingerprint,
            posted_date=payload.get("posted_date"),
            source_url=payload.get("source_url"),
            extraction_confidence=payload.get("extraction_confidence", 0.0),
            dom_snapshot=payload.get("dom_snapshot"),
        )
        db.add(job)
        db.flush()
        return job

    def run_source(self, db: Session, source_id: int, user_profile: str = "") -> PipelineResult:
        source = db.get(Source, source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        result = PipelineResult(source_id=source_id)
        breaker = self._get_breaker(source_id)
        if not breaker.can_execute():
            source.status = "paused_circuit_open"
            db.commit()
            result.errors.append("Circuit breaker open for source")
            return result

        links = self.source_engine.discover_links(source.url, source.custom_selectors)
        result.discovered_links = len(links)

        for link in links:
            try:
                html = self.source_engine.fetch_html(link)
                extracted = self.extraction_engine.extract_jobs(html, link)
                if not extracted:
                    continue

                for parsed in extracted:
                    payload = {
                        "title": parsed.job_title,
                        "location": parsed.location,
                        "remote_flag": parsed.remote_flag,
                        "salary_min": parsed.salary_min,
                        "salary_max": parsed.salary_max,
                        "description": parsed.job_description,
                        "required_skills": parsed.required_skills,
                        "seniority_level": parsed.seniority_level,
                        "employment_type": parsed.employment_type,
                        "posted_date": parsed.posted_date,
                        "apply_link": parsed.apply_link,
                        "source_url": parsed.source_url,
                        "extraction_confidence": parsed.extraction_confidence,
                        "dom_snapshot": self.extraction_engine.compress_dom(html),
                        "ingest_fingerprint": build_job_fingerprint(
                            source_id=source.id,
                            apply_link=parsed.apply_link,
                            title=parsed.job_title,
                            location=parsed.location,
                            posted_date=parsed.posted_date,
                            company_name=parsed.company_name,
                        ),
                    }

                    company = self._upsert_company(db, parsed.company_name, parsed.apply_link)
                    job = self._upsert_job(db, source, company, payload)

                    embedding: list[float] = []
                    semantic_score = 0.0
                    if user_profile.strip():
                        semantic_score, embedding = self.semantic_engine.score_job(
                            parsed.job_description,
                            user_profile,
                        )
                    else:
                        embedding = self.semantic_engine.embed_texts([parsed.job_description])[0]

                    job.semantic_score = semantic_score
                    breakdown = self.scoring_engine.compute(
                        semantic_score=semantic_score,
                        salary_min=parsed.salary_min,
                        salary_max=parsed.salary_max,
                        funding_stage=company.funding_stage,
                        company_size=company.size,
                        posted_date=parsed.posted_date,
                        remote_flag=parsed.remote_flag,
                    )
                    job.final_score = breakdown.final_score

                    self.vector_engine.upsert_embedding(db, job.id, embedding)

                    db.add(
                        ExtractionLog(
                            source_id=source.id,
                            dom_snapshot=payload["dom_snapshot"],
                            extraction_result=parsed.model_dump(mode="json"),
                            confidence_score=parsed.extraction_confidence,
                        )
                    )
                    result.extracted_jobs += 1
                    pipeline_jobs_extracted_total.labels(source_id=str(source.id)).inc()
                    db.commit()
            except Exception as exc:  # noqa: BLE001
                result.failed_links += 1
                pipeline_failures_total.labels(source_id=str(source.id)).inc()
                result.errors.append(f"{link}: {exc}")
                breaker.record_failure()
                artifacts_dir = Path("artifacts/screenshots")
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = artifacts_dir / f"source_{source.id}_{int(datetime.now().timestamp())}.png"
                saved = self.source_engine.capture_screenshot(link, str(screenshot_path))
                db.add(
                    ExtractionLog(
                        source_id=source.id,
                        error=str(exc),
                        screenshot=saved,
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                db.commit()
                self.logger.error(
                    "Link processing failed",
                    extra={"context": {"source_id": source_id, "link": link, "error": str(exc)}},
                )
                continue

        if result.failed_links == 0:
            breaker.record_success()
            source.status = "active"
        else:
            source.status = "degraded"
        source.last_run_at = datetime.now(timezone.utc)
        db.commit()
        return result
