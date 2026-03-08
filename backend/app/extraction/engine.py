from bs4 import BeautifulSoup

from app.extraction.adapters.ashby import AshbyAdapter
from app.extraction.adapters.base import ATSAdapter
from app.extraction.adapters.career_page import CareerPageAdapter
from app.extraction.adapters.greenhouse import GreenhouseAdapter
from app.extraction.adapters.indeed import IndeedAdapter
from app.extraction.adapters.lever import LeverAdapter
from app.extraction.adapters.linkedin import LinkedInAdapter
from app.extraction.adapters.naukri import NaukriAdapter
from app.extraction.adapters.workable import WorkableAdapter
from app.extraction.heuristic import HeuristicExtractor
from app.extraction.llm import LLMExtractor
from app.schemas.extraction import ExtractedJob
from app.utils.logging import get_logger


class ExtractionEngine:
    def __init__(self) -> None:
        self.logger = get_logger("extraction-engine")
        self.adapters: list[ATSAdapter] = [
            GreenhouseAdapter(),
            LeverAdapter(),
            AshbyAdapter(),
            WorkableAdapter(),
            LinkedInAdapter(),
            IndeedAdapter(),
            NaukriAdapter(),
            CareerPageAdapter(),
        ]
        self.heuristic = HeuristicExtractor()
        self.llm = LLMExtractor()

    def _dedupe(self, jobs: list[ExtractedJob]) -> list[ExtractedJob]:
        seen: set[tuple[str, str]] = set()
        deduped: list[ExtractedJob] = []
        for job in jobs:
            key = (job.job_title.lower(), (job.apply_link or "").lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(job)
        return deduped

    def extract_jobs(self, html: str, source_url: str) -> list[ExtractedJob]:
        for adapter in self.adapters:
            if adapter.can_handle(source_url, html):
                extracted = adapter.extract_jobs(html, source_url)
                if extracted:
                    self.logger.info(
                        "Adapter extraction succeeded",
                        extra={
                            "context": {
                                "source_url": source_url,
                                "adapter": adapter.platform,
                                "count": len(extracted),
                            }
                        },
                    )
                    return self._dedupe(extracted)

        heuristic_jobs = self.heuristic.extract_jobs(html, source_url)
        if heuristic_jobs:
            average_confidence = sum(job.extraction_confidence for job in heuristic_jobs) / len(
                heuristic_jobs
            )
            if average_confidence >= 0.65:
                self.logger.info(
                    "Heuristic extraction succeeded",
                    extra={
                        "context": {
                            "source_url": source_url,
                            "count": len(heuristic_jobs),
                            "confidence": round(average_confidence, 3),
                        }
                    },
                )
                return self._dedupe(heuristic_jobs)

        llm_jobs = self.llm.extract_jobs(html, source_url)
        if llm_jobs:
            self.logger.info(
                "LLM extraction succeeded",
                extra={"context": {"source_url": source_url, "count": len(llm_jobs)}},
            )
            return self._dedupe(llm_jobs)

        self.logger.warning(
            "Extraction failed",
            extra={"context": {"source_url": source_url}},
        )
        return []

    def compress_dom(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text(" ", strip=True)
        return text[:12000]
