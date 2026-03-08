from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.utils.logging import get_logger
from app.utils.retry import with_retry


@dataclass
class CompanyEnrichment:
    domain: str | None
    size: str | None
    funding_stage: str | None
    industry: str | None
    linkedin_url: str | None


class EnrichmentEngine:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.logger = get_logger("enrichment-engine")

    def extract_domain(self, url: str | None) -> str | None:
        if not url:
            return None
        parsed = urlparse(url)
        return parsed.netloc.lower() if parsed.netloc else None

    @with_retry(attempts=2)
    def _query_clearbit(self, domain: str) -> dict:
        if not self.settings.clearbit_api_key:
            return {}
        response = requests.get(
            "https://company.clearbit.com/v2/companies/find",
            params={"domain": domain},
            headers={"Authorization": f"Bearer {self.settings.clearbit_api_key}"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    @with_retry(attempts=2)
    def _scrape_homepage(self, domain: str) -> dict:
        response = requests.get(f"https://{domain}", timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else domain
        description_tag = soup.find("meta", attrs={"name": "description"})
        description = description_tag.get("content", "") if description_tag else ""
        return {"title": title, "description": description}

    def enrich(self, website_url: str | None) -> CompanyEnrichment:
        domain = self.extract_domain(website_url)
        if not domain:
            return CompanyEnrichment(
                domain=None,
                size=None,
                funding_stage=None,
                industry=None,
                linkedin_url=None,
            )

        try:
            clearbit = self._query_clearbit(domain)
            if clearbit:
                metrics = clearbit.get("metrics", {})
                category = clearbit.get("category", {})
                return CompanyEnrichment(
                    domain=domain,
                    size=str(metrics.get("employees", "")) or None,
                    funding_stage=clearbit.get("type"),
                    industry=category.get("industry"),
                    linkedin_url=clearbit.get("linkedin", {}).get("handle"),
                )
        except Exception as exc:  # noqa: BLE001
            self.logger.info(
                "Clearbit enrichment failed, switching to fallback scrape",
                extra={"context": {"domain": domain, "error": str(exc)}},
            )

        try:
            scraped = self._scrape_homepage(domain)
            return CompanyEnrichment(
                domain=domain,
                size=None,
                funding_stage=None,
                industry=scraped.get("description", "")[:120] or None,
                linkedin_url=None,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                "Fallback enrichment failed",
                extra={"context": {"domain": domain, "error": str(exc)}},
            )
            return CompanyEnrichment(
                domain=domain,
                size=None,
                funding_stage=None,
                industry=None,
                linkedin_url=None,
            )
