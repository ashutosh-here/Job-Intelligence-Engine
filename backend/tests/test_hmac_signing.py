import time

from app.utils.hmac_signing import sign_payload, verify_signature


def test_hmac_signing_roundtrip() -> None:
    payload = {"solved": True, "reason": "ok"}
    secret = "top-secret"
    timestamp = int(time.time())
    nonce = "abc123"
    signature = sign_payload(payload, secret, timestamp, nonce)
    assert verify_signature(
        payload=payload,
        secret=secret,
        timestamp=timestamp,
        nonce=nonce,
        signature=signature,
        max_skew_seconds=120,
    )


def test_hmac_signing_rejects_tampered_payload() -> None:
    payload = {"solved": True}
    secret = "top-secret"
    timestamp = int(time.time())
    nonce = "xyz789"
    signature = sign_payload(payload, secret, timestamp, nonce)
    tampered = {"solved": False}
    assert not verify_signature(
        payload=tampered,
        secret=secret,
        timestamp=timestamp,
        nonce=nonce,
        signature=signature,
        max_skew_seconds=120,
    )
