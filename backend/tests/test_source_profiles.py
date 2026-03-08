from app.sources.selectors import detect_profile, detect_strategy


def test_detect_profile_for_supported_sources() -> None:
    assert detect_profile("https://www.linkedin.com/jobs/search") is not None
    assert detect_profile("https://www.indeed.com/jobs?q=python") is not None
    assert detect_profile("https://www.naukri.com/python-jobs") is not None
    assert detect_profile("https://boards.greenhouse.io/acme") is not None
    assert detect_profile("https://jobs.lever.co/acme") is not None


def test_detect_profile_returns_default_for_unknown_domain() -> None:
    assert detect_profile("https://example.com/careers").name == "default"


def test_detect_strategy_contains_policy_metadata() -> None:
    strategy = detect_strategy("https://www.linkedin.com/jobs/search")
    assert strategy.profile.name == "linkedin"
    assert strategy.max_pages >= 5
    assert strategy.proxy_group == "linkedin"
