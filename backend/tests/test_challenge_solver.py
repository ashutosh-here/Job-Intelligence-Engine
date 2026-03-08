import time

import pytest

from app.config import Settings
from app.sources.challenge_solver import SignedHttpChallengeSolver, build_challenge_solver
from app.utils.hmac_signing import sign_payload


class _FakePage:
    def screenshot(self, full_page: bool = False):  # noqa: ARG002
        return b"img"

    def content(self):
        return "<html></html>"

    def title(self):
        return "title"


class _FakeResponse:
    def __init__(self, body: dict, headers: dict[str, str]):
        self._body = body
        self.headers = headers

    def json(self):
        return self._body

    def raise_for_status(self):
        return None


def test_build_challenge_solver_respects_provider() -> None:
    settings = Settings(
        source_challenge_solver_enabled=True,
        source_challenge_solver_provider="unsigned_http_v1",
        source_challenge_solver_endpoint="http://solver.local/solve",
    )
    solver = build_challenge_solver(settings)
    assert solver.__class__.__name__ == "UnsignedHttpChallengeSolver"


def test_signed_solver_rejects_invalid_signature() -> None:
    settings = Settings(
        source_challenge_solver_enabled=True,
        source_challenge_solver_provider="signed_http_v1",
        source_challenge_solver_endpoint="http://solver.local/solve",
        source_challenge_solver_signing_secret="secret",
    )
    solver = SignedHttpChallengeSolver(settings)
    page = _FakePage()
    response = _FakeResponse(
        body={"solved": True},
        headers={"X-JIE-Signature": "bad", "X-JIE-Timestamp": str(int(time.time())), "X-JIE-Nonce": "n1"},
    )
    with pytest.raises(ValueError):
        solver._parse_response(page, response)


def test_signed_solver_accepts_valid_signature() -> None:
    settings = Settings(
        source_challenge_solver_enabled=True,
        source_challenge_solver_provider="signed_http_v1",
        source_challenge_solver_endpoint="http://solver.local/solve",
        source_challenge_solver_signing_secret="secret",
    )
    solver = SignedHttpChallengeSolver(settings)
    page = _FakePage()
    body = {"solved": True, "reason": "passed", "actions": []}
    timestamp = int(time.time())
    nonce = "nonce123"
    signature = sign_payload(body, "secret", timestamp, nonce)
    response = _FakeResponse(
        body=body,
        headers={
            "X-JIE-Signature": signature,
            "X-JIE-Timestamp": str(timestamp),
            "X-JIE-Nonce": nonce,
        },
    )
    result = solver._parse_response(page, response)
    assert result.solved is True
    assert result.provider == "signed_http_v1"


def test_signed_solver_rejects_replay_nonce() -> None:
    settings = Settings(
        source_challenge_solver_enabled=True,
        source_challenge_solver_provider="signed_http_v1",
        source_challenge_solver_endpoint="http://solver.local/solve",
        source_challenge_solver_signing_secret="secret",
    )
    solver = SignedHttpChallengeSolver(settings)
    page = _FakePage()
    body = {"solved": True, "actions": []}
    timestamp = int(time.time())
    nonce = "fixed-nonce"
    signature = sign_payload(body, "secret", timestamp, nonce)
    headers = {
        "X-JIE-Signature": signature,
        "X-JIE-Timestamp": str(timestamp),
        "X-JIE-Nonce": nonce,
    }

    first = _FakeResponse(body=body, headers=headers)
    second = _FakeResponse(body=body, headers=headers)
    assert solver._parse_response(page, first).solved is True
    with pytest.raises(ValueError):
        solver._parse_response(page, second)
