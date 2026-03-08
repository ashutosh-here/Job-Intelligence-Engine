from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SignedEnvelope:
    payload: dict[str, Any]
    timestamp: int
    nonce: str
    signature: str


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=True)


def build_message(payload: dict[str, Any], timestamp: int, nonce: str) -> bytes:
    return f"{timestamp}.{nonce}.{canonical_json(payload)}".encode("utf-8")


def sign_payload(payload: dict[str, Any], secret: str, timestamp: int, nonce: str) -> str:
    message = build_message(payload, timestamp, nonce)
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return digest


def verify_signature(
    payload: dict[str, Any],
    secret: str,
    timestamp: int,
    nonce: str,
    signature: str,
    max_skew_seconds: int = 120,
    now_epoch: int | None = None,
) -> bool:
    now = now_epoch if now_epoch is not None else int(time.time())
    if abs(now - timestamp) > max(5, max_skew_seconds):
        return False
    expected = sign_payload(payload, secret, timestamp, nonce)
    return hmac.compare_digest(expected, signature)
