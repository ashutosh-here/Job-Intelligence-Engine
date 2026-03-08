from app.sources.selectors import apply_strategy_overrides, detect_strategy


def test_strategy_override_injects_custom_selectors() -> None:
    strategy = detect_strategy("https://www.indeed.com/jobs?q=python")
    overridden = apply_strategy_overrides(
        strategy,
        {
            "job_links": "a.custom-job-link",
            "next_page": "button.custom-next",
            "strategy_max_pages": "12",
            "strategy_max_scrolls": "2",
        },
    )
    assert overridden.profile.job_link_selectors[0] == "a.custom-job-link"
    assert overridden.profile.next_page_selectors[0] == "button.custom-next"
    assert overridden.max_pages == 12
    assert overridden.max_scrolls == 2
