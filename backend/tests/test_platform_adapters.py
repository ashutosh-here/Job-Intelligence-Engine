from pathlib import Path

import pytest

from app.extraction.adapters.greenhouse import GreenhouseAdapter
from app.extraction.adapters.indeed import IndeedAdapter
from app.extraction.adapters.lever import LeverAdapter
from app.extraction.adapters.linkedin import LinkedInAdapter
from app.extraction.adapters.naukri import NaukriAdapter


FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("adapter", "fixture", "source_url", "expected_title"),
    [
        (GreenhouseAdapter(), "greenhouse_sample.html", "https://boards.greenhouse.io/acme", "Platform Engineer"),
        (LeverAdapter(), "lever_sample.html", "https://jobs.lever.co/acme", "Senior Backend Engineer"),
        (LinkedInAdapter(), "linkedin_sample.html", "https://www.linkedin.com/jobs/search", "Machine Learning Engineer"),
        (IndeedAdapter(), "indeed_sample.html", "https://www.indeed.com/jobs?q=engineer", "Data Engineer"),
        (NaukriAdapter(), "naukri_sample.html", "https://www.naukri.com/python-jobs", "Backend Engineer"),
    ],
)
def test_platform_adapters_extract_expected_roles(adapter, fixture, source_url, expected_title) -> None:
    html = (FIXTURE_DIR / fixture).read_text(encoding="utf-8")
    assert adapter.can_handle(source_url, html)
    jobs = adapter.extract_jobs(html, source_url)
    assert jobs, f"No jobs extracted for {adapter.platform}"
    assert any(expected_title.lower() in job.job_title.lower() for job in jobs)


def test_indeed_adapter_resolves_relative_apply_url() -> None:
    html = (FIXTURE_DIR / "indeed_sample.html").read_text(encoding="utf-8")
    adapter = IndeedAdapter()
    jobs = adapter.extract_jobs(html, "https://www.indeed.com/jobs?q=engineer")
    assert jobs
    assert jobs[0].apply_link.startswith("https://www.indeed.com")
