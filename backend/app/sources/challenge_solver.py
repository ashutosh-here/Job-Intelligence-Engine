from __future__ import annotations

import base64
import secrets
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import requests
from playwright.sync_api import Page

from app.config import Settings, get_settings
from app.utils.hmac_signing import sign_payload, verify_signature
from app.utils.logging import get_logger


@dataclass
class ChallengeSolveResult:
    solved: bool
    provider: str
    reason: str = ""
    action_count: int = 0


class ChallengeSolver(ABC):
    @abstractmethod
    def solve(self, page: Page, source_url: str) -> ChallengeSolveResult: ...


class NoopChallengeSolver(ChallengeSolver):
    def solve(self, page: Page, source_url: str) -> ChallengeSolveResult:
        return ChallengeSolveResult(
            solved=False,
            provider="noop",
            reason="No challenge solver configured",
        )


class BaseHttpChallengeSolver(ChallengeSolver):
    provider_name = "http"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.logger = get_logger("challenge-solver")

    def _build_payload(self, page: Page, source_url: str) -> dict[str, Any]:
        screenshot = page.screenshot(full_page=True)
        html = page.content()[:15000]
        return {
            "source_url": source_url,
            "html": html,
            "title": page.title(),
            "screenshot_base64": base64.b64encode(screenshot).decode("utf-8"),
        }

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.source_challenge_solver_api_key:
            headers["Authorization"] = f"Bearer {self.settings.source_challenge_solver_api_key}"
        return headers

    def _post_solver(self, payload: dict[str, Any], headers: dict[str, str]) -> requests.Response:
        if (
            self.settings.environment == "prod"
            and not self.settings.source_challenge_solver_endpoint.lower().startswith("https://")
        ):
            raise ValueError("In production, source_challenge_solver_endpoint must use HTTPS")
        return requests.post(
            self.settings.source_challenge_solver_endpoint,
            json=payload,
            headers=headers,
            timeout=20,
        )

    def _execute_actions(self, page: Page, actions: list[dict[str, Any]]) -> int:
        applied = 0
        for action in actions[:8]:
            action_type = (action.get("type") or "").lower()
            try:
                if action_type == "click":
                    selector = str(action["selector"])
                    page.click(selector, timeout=5000)
                    applied += 1
                elif action_type == "fill":
                    selector = str(action["selector"])
                    value = str(action.get("value", ""))
                    page.fill(selector, value, timeout=5000)
                    applied += 1
                elif action_type == "wait":
                    ms = int(action.get("milliseconds", 2000))
                    page.wait_for_timeout(max(100, min(ms, 15000)))
                    applied += 1
                elif action_type == "set_cookie":
                    cookie = action.get("cookie", {})
                    if cookie.get("name") and cookie.get("value"):
                        page.context.add_cookies([cookie])
                        applied += 1
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(
                    "Challenge action execution failed",
                    extra={"context": {"action": action_type, "error": str(exc)}},
                )
                continue
        return applied

    def _parse_response(self, page: Page, response: requests.Response) -> ChallengeSolveResult:
        response.raise_for_status()
        body = response.json()
        actions = body.get("actions") if isinstance(body.get("actions"), list) else []
        action_count = self._execute_actions(page, actions)
        solved = bool(body.get("solved", False))
        return ChallengeSolveResult(
            solved=solved,
            provider=self.provider_name,
            reason=str(body.get("reason", "")),
            action_count=action_count,
        )

    def solve(self, page: Page, source_url: str) -> ChallengeSolveResult:
        if not self.settings.source_challenge_solver_endpoint:
            return ChallengeSolveResult(False, self.provider_name, "Solver endpoint not configured")

        try:
            payload = self._build_payload(page, source_url)
            headers = self._headers()
            response = self._post_solver(payload, headers)
            return self._parse_response(page, response)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                "Challenge solver request failed",
                extra={"context": {"source_url": source_url, "error": str(exc)}},
            )
            return ChallengeSolveResult(False, self.provider_name, str(exc))


class SignedHttpChallengeSolver(BaseHttpChallengeSolver):
    provider_name = "signed_http_v1"

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings)
        self._seen_response_nonces: dict[str, int] = {}

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        headers["X-JIE-Provider"] = self.provider_name
        return headers

    def _post_solver(self, payload: dict[str, Any], headers: dict[str, str]) -> requests.Response:
        secret = self.settings.source_challenge_solver_signing_secret
        if not secret:
            raise ValueError("source_challenge_solver_signing_secret is required for signed provider")

        timestamp = int(time.time())
        nonce = secrets.token_hex(12)
        signature = sign_payload(payload, secret=secret, timestamp=timestamp, nonce=nonce)
        headers = {
            **headers,
            "X-JIE-Timestamp": str(timestamp),
            "X-JIE-Nonce": nonce,
            "X-JIE-Signature": signature,
        }
        return super()._post_solver(payload, headers)

    def _parse_response(self, page: Page, response: requests.Response) -> ChallengeSolveResult:
        secret = self.settings.source_challenge_solver_signing_secret
        try:
            body = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Challenge solver returned non-JSON response") from exc

        signature = response.headers.get("X-JIE-Signature", "")
        timestamp_raw = response.headers.get("X-JIE-Timestamp", "0")
        nonce = response.headers.get("X-JIE-Nonce", "")
        if not signature or not nonce:
            raise ValueError("Missing signed response headers")
        try:
            timestamp = int(timestamp_raw)
        except ValueError as exc:
            raise ValueError("Invalid signed response timestamp") from exc

        now = int(time.time())
        self._seen_response_nonces = {
            key: seen_at for key, seen_at in self._seen_response_nonces.items() if now - seen_at <= 600
        }
        if nonce in self._seen_response_nonces:
            raise ValueError("Replay detected: response nonce already used")
        self._seen_response_nonces[nonce] = now

        if not verify_signature(
            payload=body,
            secret=secret,
            timestamp=timestamp,
            nonce=nonce,
            signature=signature,
            max_skew_seconds=self.settings.source_challenge_response_max_skew_seconds,
        ):
            raise ValueError("Signed response validation failed")

        # Reuse base parser against already-decoded JSON body through synthetic response adapter.
        actions = body.get("actions") if isinstance(body.get("actions"), list) else []
        action_count = self._execute_actions(page, actions)
        solved = bool(body.get("solved", False))
        return ChallengeSolveResult(
            solved=solved,
            provider=self.provider_name,
            reason=str(body.get("reason", "")),
            action_count=action_count,
        )


class UnsignedHttpChallengeSolver(BaseHttpChallengeSolver):
    provider_name = "unsigned_http_v1"


def build_challenge_solver(settings: Settings | None = None) -> ChallengeSolver:
    cfg = settings or get_settings()
    if not cfg.source_challenge_solver_enabled:
        return NoopChallengeSolver()

    provider = cfg.source_challenge_solver_provider.lower().strip()
    if provider == "signed_http_v1":
        return SignedHttpChallengeSolver(cfg)
    if provider == "unsigned_http_v1":
        return UnsignedHttpChallengeSolver(cfg)
    return SignedHttpChallengeSolver(cfg)
