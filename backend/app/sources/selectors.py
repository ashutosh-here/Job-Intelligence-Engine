from dataclasses import dataclass, replace


@dataclass(frozen=True)
class DiscoveryProfile:
    name: str
    job_link_selectors: tuple[str, ...]
    next_page_selectors: tuple[str, ...]
    requires_scroll: bool = True


@dataclass(frozen=True)
class BrowserStrategy:
    profile: DiscoveryProfile
    max_pages: int
    max_scrolls: int
    min_delay_seconds: float
    max_delay_seconds: float
    rotate_user_agent: bool = True
    block_resource_types: tuple[str, ...] = ("image", "font", "media")
    use_persistent_session: bool = True
    challenge_markers: tuple[str, ...] = (
        "captcha",
        "are you human",
        "access denied",
        "cloudflare",
        "bot detection",
        "verify you are a human",
    )
    proxy_group: str | None = None


DISCOVERY_PROFILES: dict[str, DiscoveryProfile] = {
    "default": DiscoveryProfile(
        name="default",
        job_link_selectors=("a[href]",),
        next_page_selectors=("a[rel='next']", "button[aria-label*='Next']", "a:has-text('Next')"),
        requires_scroll=True,
    ),
    "linkedin": DiscoveryProfile(
        name="linkedin",
        job_link_selectors=(
            "a.base-card__full-link",
            "a[href*='/jobs/view/']",
            "a.job-card-list__title",
        ),
        next_page_selectors=("button[aria-label='Next']", "button.artdeco-pagination__button--next"),
    ),
    "indeed": DiscoveryProfile(
        name="indeed",
        job_link_selectors=("a.jcs-JobTitle", "a[href*='/viewjob']", "a[data-jk]"),
        next_page_selectors=("a[data-testid='pagination-page-next']", "a[aria-label='Next Page']"),
    ),
    "naukri": DiscoveryProfile(
        name="naukri",
        job_link_selectors=("a.title", "a[href*='/job-listings-']", "a[href*='/jobs/']"),
        next_page_selectors=("a[title='Next']", "a.styles_btn-secondary__2AsIP"),
    ),
    "greenhouse": DiscoveryProfile(
        name="greenhouse",
        job_link_selectors=("a.opening", "a[href*='greenhouse.io']"),
        next_page_selectors=("a[rel='next']",),
        requires_scroll=False,
    ),
    "lever": DiscoveryProfile(
        name="lever",
        job_link_selectors=("a.posting-title", "a[href*='lever.co']"),
        next_page_selectors=("a[rel='next']",),
        requires_scroll=False,
    ),
}


STRATEGIES: dict[str, BrowserStrategy] = {
    "default": BrowserStrategy(
        profile=DISCOVERY_PROFILES["default"],
        max_pages=5,
        max_scrolls=6,
        min_delay_seconds=0.3,
        max_delay_seconds=1.2,
    ),
    "linkedin": BrowserStrategy(
        profile=DISCOVERY_PROFILES["linkedin"],
        max_pages=8,
        max_scrolls=8,
        min_delay_seconds=0.45,
        max_delay_seconds=1.6,
        proxy_group="linkedin",
    ),
    "indeed": BrowserStrategy(
        profile=DISCOVERY_PROFILES["indeed"],
        max_pages=8,
        max_scrolls=5,
        min_delay_seconds=0.35,
        max_delay_seconds=1.3,
        proxy_group="indeed",
    ),
    "naukri": BrowserStrategy(
        profile=DISCOVERY_PROFILES["naukri"],
        max_pages=10,
        max_scrolls=4,
        min_delay_seconds=0.25,
        max_delay_seconds=1.0,
        proxy_group="naukri",
    ),
    "greenhouse": BrowserStrategy(
        profile=DISCOVERY_PROFILES["greenhouse"],
        max_pages=5,
        max_scrolls=0,
        min_delay_seconds=0.2,
        max_delay_seconds=0.8,
        proxy_group="ats",
    ),
    "lever": BrowserStrategy(
        profile=DISCOVERY_PROFILES["lever"],
        max_pages=5,
        max_scrolls=0,
        min_delay_seconds=0.2,
        max_delay_seconds=0.8,
        proxy_group="ats",
    ),
}


def detect_profile(source_url: str) -> DiscoveryProfile | None:
    return detect_strategy(source_url).profile


def detect_strategy(source_url: str) -> BrowserStrategy:
    normalized = source_url.lower()
    if "linkedin.com" in normalized:
        return STRATEGIES["linkedin"]
    if "indeed." in normalized:
        return STRATEGIES["indeed"]
    if "naukri.com" in normalized:
        return STRATEGIES["naukri"]
    if "greenhouse.io" in normalized:
        return STRATEGIES["greenhouse"]
    if "lever.co" in normalized:
        return STRATEGIES["lever"]
    return STRATEGIES["default"]


def apply_strategy_overrides(
    strategy: BrowserStrategy,
    custom_selectors: dict[str, str] | None,
) -> BrowserStrategy:
    if not custom_selectors:
        return strategy

    profile = strategy.profile
    if custom_selectors.get("job_links"):
        profile = replace(
            profile,
            job_link_selectors=(custom_selectors["job_links"],) + tuple(profile.job_link_selectors),
        )
    if custom_selectors.get("next_page"):
        profile = replace(
            profile,
            next_page_selectors=(custom_selectors["next_page"],) + tuple(profile.next_page_selectors),
        )

    max_pages = int(custom_selectors.get("strategy_max_pages", strategy.max_pages))
    max_scrolls = int(custom_selectors.get("strategy_max_scrolls", strategy.max_scrolls))
    min_delay = float(custom_selectors.get("strategy_min_delay", strategy.min_delay_seconds))
    max_delay = float(custom_selectors.get("strategy_max_delay", strategy.max_delay_seconds))
    return replace(
        strategy,
        profile=profile,
        max_pages=max_pages,
        max_scrolls=max_scrolls,
        min_delay_seconds=min_delay,
        max_delay_seconds=max_delay,
    )
