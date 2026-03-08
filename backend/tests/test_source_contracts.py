import json
from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from app.extraction.adapters.greenhouse import GreenhouseAdapter
from app.extraction.adapters.indeed import IndeedAdapter
from app.extraction.adapters.linkedin import LinkedInAdapter
from app.extraction.adapters.naukri import NaukriAdapter


CONTRACTS_PATH = Path(__file__).parent / "contracts" / "source_contracts.json"
ROOT = Path(__file__).resolve().parents[1]

ADAPTERS = {
    "linkedin": LinkedInAdapter(),
    "indeed": IndeedAdapter(),
    "naukri": NaukriAdapter(),
    "greenhouse": GreenhouseAdapter(),
}


def load_contracts() -> list[dict]:
    return json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("contract", load_contracts(), ids=lambda c: c["name"])
@pytest.mark.contract
def test_recorded_source_contract(contract: dict) -> None:
    adapter = ADAPTERS[contract["adapter"]]
    fixture_path = ROOT / contract["fixture"]
    html = fixture_path.read_text(encoding="utf-8")
    source_url = contract["source_url"]

    assert adapter.can_handle(source_url, html), f"Adapter {adapter.platform} no longer recognizes source URL"

    soup = BeautifulSoup(html, "html.parser")
    for selector_key in contract["required_selector_keys"]:
        selector = adapter.selectors.get(selector_key)
        assert selector, f"Missing selector key '{selector_key}' on adapter {adapter.platform}"
        matches = soup.select(selector)
        assert (
            len(matches) > 0
        ), f"Selector drift detected: {adapter.platform}.{selector_key}='{selector}' no longer matches recorded page"

    jobs = adapter.extract_jobs(html, source_url)
    assert len(jobs) >= contract["min_jobs"], f"Extraction contract failed for {adapter.platform}"

    for field in contract["required_job_fields"]:
        assert any(getattr(job, field) for job in jobs), f"Required field '{field}' empty for {adapter.platform}"
