from app.config import Settings
from app.sources.proxy_pool import ProxyPool


def test_proxy_pool_parses_grouped_proxies() -> None:
    settings = Settings(
        source_enable_proxy_rotation=True,
        source_proxies=[
            "linkedin|indeed=http://user:pass@proxy1:8080",
            "default=http://proxy2:8080",
        ],
    )
    pool = ProxyPool.from_settings(settings)
    assert len(pool.endpoints) == 2
    assert "linkedin" in pool.endpoints[0].groups
    assert pool.endpoints[0].username == "user"
    assert pool.endpoints[0].password == "pass"


def test_proxy_pool_cooldown_after_failures() -> None:
    settings = Settings(
        source_enable_proxy_rotation=True,
        source_proxies=["naukri=http://proxy3:8080"],
        source_proxy_max_failures=2,
        source_proxy_cooldown_seconds=60,
    )
    pool = ProxyPool.from_settings(settings)
    proxy = pool.acquire("www.naukri.com", "naukri")
    assert proxy is not None
    pool.report_failure(proxy, "blocked")
    pool.report_failure(proxy, "blocked")
    assert proxy.available() is False
