from abc import ABC, abstractmethod
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.extraction.common import infer_remote_flag, infer_required_skills, parse_posted_date, parse_salary
from app.schemas.extraction import ExtractedJob


class ATSAdapter(ABC):
    platform: str

    @abstractmethod
    def can_handle(self, source_url: str, html: str) -> bool: ...

    @abstractmethod
    def extract_jobs(self, html: str, source_url: str) -> list[ExtractedJob]: ...


class GenericCssAdapter(ATSAdapter):
    platform = "generic"
    url_markers: tuple[str, ...] = ()
    selectors: dict[str, str] = {}
    default_company: str = "Unknown"

    def can_handle(self, source_url: str, html: str) -> bool:
        haystack = f"{source_url.lower()} {html[:2000].lower()}"
        return any(marker in haystack for marker in self.url_markers)

    def extract_jobs(self, html: str, source_url: str) -> list[ExtractedJob]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(self.selectors["card"])
        extracted: list[ExtractedJob] = []

        for card in cards:
            title = (card.select_one(self.selectors["title"]) or card).get_text(" ", strip=True)
            company_el = card.select_one(self.selectors.get("company", ""))
            location_el = card.select_one(self.selectors.get("location", ""))
            apply_el = card.select_one(self.selectors.get("apply", "a[href]"))
            desc_el = card.select_one(self.selectors.get("description", ""))
            posted_el = card.select_one(self.selectors.get("posted_date", ""))

            description = desc_el.get_text(" ", strip=True) if desc_el else card.get_text(" ", strip=True)
            salary_min, salary_max = parse_salary(description)
            company_name = self.default_company
            if company_el:
                company_name = company_el.get("content") or company_el.get_text(" ", strip=True)
            apply_link = apply_el.get("href") if apply_el else source_url
            apply_link = urljoin(source_url, apply_link) if apply_link else source_url

            extracted.append(
                ExtractedJob(
                    job_title=title[:300] if title else "Unknown Role",
                    company_name=company_name,
                    location=location_el.get_text(" ", strip=True) if location_el else None,
                    remote_flag=infer_remote_flag(description),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    job_description=description[:12000],
                    required_skills=infer_required_skills(description),
                    seniority_level=None,
                    employment_type=None,
                    posted_date=parse_posted_date(posted_el.get_text(" ", strip=True)) if posted_el else None,
                    apply_link=apply_link,
                    source_url=source_url,
                    extraction_confidence=0.78,
                )
            )
        return extracted
