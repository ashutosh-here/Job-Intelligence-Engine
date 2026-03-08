import json
import re

import requests

from app.config import Settings, get_settings
from app.schemas.extraction import ExtractedJob
from app.utils.logging import get_logger
from app.utils.retry import with_retry


class LLMExtractor:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.logger = get_logger("llm-extractor")

    def clean_dom_text(self, html: str) -> str:
        compact = re.sub(r"<script.*?>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        compact = re.sub(r"<style.*?>.*?</style>", " ", compact, flags=re.DOTALL | re.IGNORECASE)
        compact = re.sub(r"<[^>]+>", " ", compact)
        compact = re.sub(r"\s+", " ", compact)
        return compact[:12000]

    @with_retry(attempts=2)
    def _call_local_llm(self, prompt: str) -> str:
        payload = {
            "model": self.settings.local_llm_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        response = requests.post(
            self.settings.local_llm_endpoint,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        body = response.json()
        return body.get("response", "{}")

    def extract_jobs(self, html: str, source_url: str) -> list[ExtractedJob]:
        cleaned = self.clean_dom_text(html)
        prompt = (
            "Extract structured job information from this text. "
            "Return strict JSON array with keys: "
            "job_title, company_name, location, remote_flag, salary_min, salary_max, "
            "job_description, required_skills, seniority_level, employment_type, posted_date, "
            "apply_link, source_url, extraction_confidence. "
            f"Text: {cleaned}"
        )

        try:
            raw = self._call_local_llm(prompt)
            parsed = json.loads(raw)
            items = parsed if isinstance(parsed, list) else [parsed]
            validated: list[ExtractedJob] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                item["source_url"] = source_url
                validated.append(ExtractedJob.model_validate(item))
            if validated:
                return validated
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                "LLM extraction failed",
                extra={"context": {"source_url": source_url, "error": str(exc)}},
            )
        return []
