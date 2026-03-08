from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.config import Settings, get_settings
from app.utils.logging import get_logger


@dataclass
class ProxyEndpoint:
    server: str
    username: str | None = None
    password: str | None = None
    groups: set[str] = field(default_factory=set)
    failure_count: int = 0
    success_count: int = 0
    cooldown_until: datetime | None = None

    def available(self) -> bool:
        if self.cooldown_until is None:
            return True
        return datetime.now(timezone.utc) >= self.cooldown_until

    def as_playwright_proxy(self) -> dict[str, str]:
        payload = {"server": self.server}
        if self.username:
            payload["username"] = self.username
        if self.password:
            payload["password"] = self.password
        return payload


class ProxyPool:
    def __init__(self, endpoints: list[ProxyEndpoint], settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.endpoints = endpoints
        self.logger = get_logger("proxy-pool")
        self._lock = Lock()
        self._sticky_assignments: dict[str, tuple[str, datetime]] = {}

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> ProxyPool:
        cfg = settings or get_settings()
        endpoints: list[ProxyEndpoint] = []

        for raw in cfg.source_proxies:
            # Supported formats:
            # - "https://user:pass@proxy:8080"
            # - "linkedin=https://proxy:8080"
            # - "linkedin|indeed=https://proxy:8080"
            groups: set[str] = set()
            server_part = raw.strip()
            if "=" in server_part:
                groups_raw, server_part = server_part.split("=", 1)
                groups = {chunk.strip().lower() for chunk in groups_raw.split("|") if chunk.strip()}

            username = None
            password = None
            server = server_part.strip()
            if "@" in server and "://" in server:
                scheme, rest = server.split("://", 1)
                creds, host = rest.split("@", 1)
                if ":" in creds:
                    username, password = creds.split(":", 1)
                server = f"{scheme}://{host}"

            if server:
                endpoints.append(
                    ProxyEndpoint(
                        server=server,
                        username=username,
                        password=password,
                        groups=groups,
                    )
                )
        return cls(endpoints=endpoints, settings=cfg)

    def acquire(self, domain: str, group: str | None = None) -> ProxyEndpoint | None:
        if not self.settings.source_enable_proxy_rotation:
            return None

        with self._lock:
            sticky = self._sticky_assignments.get(domain)
            if sticky:
                server, until = sticky
                if until > datetime.now(timezone.utc):
                    existing = next((proxy for proxy in self.endpoints if proxy.server == server), None)
                    if existing and existing.available():
                        return existing

            candidates = [proxy for proxy in self.endpoints if proxy.available()]
            if group:
                group_lower = group.lower()
                grouped = [proxy for proxy in candidates if group_lower in proxy.groups]
                if grouped:
                    candidates = grouped
            if not candidates:
                return None

            selected = random.choice(candidates)
            sticky_until = datetime.now(timezone.utc) + timedelta(
                minutes=max(1, self.settings.source_proxy_sticky_minutes)
            )
            self._sticky_assignments[domain] = (selected.server, sticky_until)
            return selected

    def report_success(self, proxy: ProxyEndpoint | None) -> None:
        if proxy is None:
            return
        with self._lock:
            proxy.success_count += 1
            proxy.failure_count = 0
            proxy.cooldown_until = None

    def report_failure(self, proxy: ProxyEndpoint | None, error: str = "") -> None:
        if proxy is None:
            return
        with self._lock:
            proxy.failure_count += 1
            if proxy.failure_count >= self.settings.source_proxy_max_failures:
                proxy.cooldown_until = datetime.now(timezone.utc) + timedelta(
                    seconds=max(30, self.settings.source_proxy_cooldown_seconds)
                )
                self.logger.warning(
                    "Proxy cooled down after failures",
                    extra={
                        "context": {
                            "proxy": proxy.server,
                            "failures": proxy.failure_count,
                            "cooldown_until": proxy.cooldown_until.isoformat(),
                            "error": error,
                        }
                    },
                )
