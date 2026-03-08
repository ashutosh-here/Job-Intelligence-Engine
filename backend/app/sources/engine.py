from __future__ import annotations

import random
import re
import time
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, sync_playwright

from app.config import Settings, get_settings
from app.sources.challenge_solver import ChallengeSolver, build_challenge_solver
from app.sources.proxy_pool import ProxyEndpoint, ProxyPool
from app.sources.selectors import BrowserStrategy, apply_strategy_overrides, detect_strategy
from app.utils.logging import get_logger
from app.utils.retry import with_retry


class SourceEngine:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.logger = get_logger("source-engine")
        self._job_hint_pattern = re.compile(
            r"(job|career|opening|position|vacanc|apply|developer|engineer|data-scientist)",
            re.IGNORECASE,
        )
        self._last_request_at: dict[str, float] = {}
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        ]
        self.proxy_pool = ProxyPool.from_settings(self.settings)
        self.challenge_solver: ChallengeSolver = build_challenge_solver(self.settings)

    def _human_delay(self, minimum: float = 0.3, maximum: float = 1.2) -> None:
        time.sleep(random.uniform(minimum, maximum))

    def _rate_limit(self, domain: str) -> None:
        interval = 60.0 / max(1, self.settings.source_rate_limit_per_minute)
        now = time.monotonic()
        last = self._last_request_at.get(domain)
        if last is not None:
            wait = interval - (now - last)
            if wait > 0:
                time.sleep(wait + random.uniform(0.05, 0.2))
        self._last_request_at[domain] = time.monotonic()

    def _normalize_links(self, links: Iterable[str], base_url: str) -> list[str]:
        normalized: set[str] = set()
        for link in links:
            if not link:
                continue
            absolute = urljoin(base_url, link)
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            normalized.add(absolute)
        return sorted(normalized)

    def _is_likely_job_link(self, url: str) -> bool:
        return bool(self._job_hint_pattern.search(url))

    def _new_context(
        self,
        playwright,
        source_url: str,
        strategy: BrowserStrategy,
        proxy: ProxyEndpoint | None,
    ):
        state_dir = Path(self.settings.source_session_state_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
        domain = urlparse(source_url).netloc.replace(":", "_") or "default"
        storage_state_path = state_dir / f"{domain}.json"

        rotate_user_agent = strategy.rotate_user_agent and self.settings.source_rotate_user_agents
        user_agent = random.choice(self._user_agents) if rotate_user_agent else None

        launch_args = ["--disable-blink-features=AutomationControlled"]
        launch_kwargs = {"headless": True, "args": launch_args}
        if proxy:
            launch_kwargs["proxy"] = proxy.as_playwright_proxy()

        browser = playwright.chromium.launch(**launch_kwargs)
        context_args = {
            "viewport": {
                "width": random.choice([1280, 1366, 1440]),
                "height": random.choice([720, 768, 900]),
            },
            "ignore_https_errors": True,
            "locale": "en-US",
            "timezone_id": "UTC",
        }
        if user_agent:
            context_args["user_agent"] = user_agent
        if strategy.use_persistent_session and storage_state_path.exists():
            context_args["storage_state"] = str(storage_state_path)

        context = browser.new_context(**context_args)
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        context.set_extra_http_headers(
            {
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        blocked_types = set(strategy.block_resource_types) or set(self.settings.source_block_resource_types)
        context.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in blocked_types
            else route.continue_(),
        )
        return browser, context, storage_state_path

    def _collect_links_from_selectors(self, page: Page, selectors: Iterable[str]) -> set[str]:
        links: set[str] = set()
        for selector in selectors:
            try:
                hrefs = page.eval_on_selector_all(
                    selector,
                    "elements => elements.map(el => el.getAttribute('href'))",
                )
                for href in hrefs:
                    if href:
                        links.add(href)
            except Exception:  # noqa: BLE001
                continue
        return links

    def _detect_bot_wall(self, html: str, strategy: BrowserStrategy) -> bool:
        lower = html[:12000].lower()
        return any(marker in lower for marker in strategy.challenge_markers)

    def _navigate_page(self, page: Page, url: str, strategy: BrowserStrategy) -> None:
        page.goto(
            url,
            timeout=self.settings.source_request_timeout_seconds * 1000,
            wait_until="domcontentloaded",
        )
        self._human_delay(strategy.min_delay_seconds, strategy.max_delay_seconds)

    def _try_next_page(self, page: Page, selectors: Iterable[str], strategy: BrowserStrategy) -> bool:
        for selector in selectors:
            if not selector:
                continue
            button = page.query_selector(selector)
            if button:
                button.click()
                self._human_delay(strategy.min_delay_seconds, strategy.max_delay_seconds)
                return True
        return False

    def _attempt_challenge_resolution(
        self,
        page: Page,
        source_url: str,
        strategy: BrowserStrategy,
    ) -> bool:
        attempts = max(1, self.settings.source_challenge_retry_limit)
        for _ in range(attempts):
            solved = self.challenge_solver.solve(page, source_url)
            self.logger.warning(
                "Challenge solver attempted",
                extra={
                    "context": {
                        "source_url": source_url,
                        "provider": solved.provider,
                        "solved": solved.solved,
                        "reason": solved.reason,
                        "actions": solved.action_count,
                    }
                },
            )
            if solved.solved:
                self._human_delay(strategy.min_delay_seconds, strategy.max_delay_seconds)
                html = page.content()
                if not self._detect_bot_wall(html, strategy):
                    return True
        return False

    @with_retry(attempts=3)
    def discover_links(
        self, source_url: str, custom_selectors: dict[str, str] | None = None
    ) -> list[str]:
        self.logger.info("Starting discovery for source", extra={"context": {"source_url": source_url}})
        links: set[str] = set()
        strategy = apply_strategy_overrides(detect_strategy(source_url), custom_selectors)
        domain = urlparse(source_url).netloc.lower()
        self._rate_limit(domain)
        proxy = self.proxy_pool.acquire(domain, strategy.proxy_group)

        with sync_playwright() as p:
            browser, context, state_path = self._new_context(p, source_url, strategy, proxy)
            try:
                page = context.new_page()
                self._navigate_page(page, source_url, strategy)
                if self._detect_bot_wall(page.content(), strategy):
                    if not self._attempt_challenge_resolution(page, source_url, strategy):
                        raise RuntimeError(f"Bot wall detected for {source_url}")

                max_pages = min(strategy.max_pages, self.settings.source_max_pages + 5)
                for _ in range(max_pages):
                    if strategy.profile.requires_scroll and strategy.max_scrolls > 0:
                        for _ in range(strategy.max_scrolls):
                            page.mouse.wheel(0, random.randint(4000, 22000))
                            self._human_delay(
                                max(0.1, strategy.min_delay_seconds * 0.5),
                                max(0.25, strategy.max_delay_seconds * 0.75),
                            )

                    baseline_hrefs = self._collect_links_from_selectors(page, ("a[href]",))
                    for href in baseline_hrefs:
                        if href and self._is_likely_job_link(href):
                            links.add(href)

                    for href in self._collect_links_from_selectors(
                        page, strategy.profile.job_link_selectors
                    ):
                        if href:
                            links.add(href)

                    clicked_next = self._try_next_page(
                        page,
                        strategy.profile.next_page_selectors,
                        strategy,
                    )
                    if not clicked_next:
                        break

                if strategy.use_persistent_session:
                    context.storage_state(path=str(state_path))
                page.close()
                self.proxy_pool.report_success(proxy)
            except Exception as exc:  # noqa: BLE001
                self.proxy_pool.report_failure(proxy, str(exc))
                raise
            finally:
                context.close()
                browser.close()

        discovered = self._normalize_links(links, source_url)
        self.logger.info(
            "Discovery complete",
            extra={
                "context": {
                    "source_url": source_url,
                    "count": len(discovered),
                    "strategy": strategy.profile.name,
                    "proxy": proxy.server if proxy else None,
                }
            },
        )
        return discovered

    @with_retry(attempts=3)
    def fetch_html(self, url: str) -> str:
        domain = urlparse(url).netloc.lower()
        strategy = detect_strategy(url)
        self._rate_limit(domain)
        proxy = self.proxy_pool.acquire(domain, strategy.proxy_group)
        with sync_playwright() as p:
            browser, context, state_path = self._new_context(p, url, strategy, proxy)
            try:
                page = context.new_page()
                self._navigate_page(page, url, strategy)
                html = page.content()
                if self._detect_bot_wall(html, strategy):
                    solved = self._attempt_challenge_resolution(page, url, strategy)
                    if not solved:
                        raise RuntimeError(f"Bot wall detected for {url}")
                    html = page.content()
                if strategy.use_persistent_session:
                    context.storage_state(path=str(state_path))
                page.close()
                self.proxy_pool.report_success(proxy)
                return html
            except Exception as exc:  # noqa: BLE001
                self.proxy_pool.report_failure(proxy, str(exc))
                raise
            finally:
                context.close()
                browser.close()

    def capture_screenshot(self, url: str, output_path: str) -> str | None:
        strategy = detect_strategy(url)
        domain = urlparse(url).netloc.lower()
        proxy = self.proxy_pool.acquire(domain, strategy.proxy_group)
        try:
            with sync_playwright() as p:
                browser, context, state_path = self._new_context(p, url, strategy, proxy)
                page = context.new_page()
                self._navigate_page(page, url, strategy)
                page.screenshot(path=output_path, full_page=True)
                if strategy.use_persistent_session:
                    context.storage_state(path=str(state_path))
                page.close()
                context.close()
                browser.close()
            self.proxy_pool.report_success(proxy)
            return output_path
        except Exception as exc:  # noqa: BLE001
            self.proxy_pool.report_failure(proxy, str(exc))
            return None
