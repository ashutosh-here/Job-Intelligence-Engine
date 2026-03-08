import pytest

from app.auth.security import create_access_token, decode_token, hash_password, verify_password


def test_password_hash_and_verify() -> None:
    raw = "super-secure-password"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip() -> None:
    token = create_access_token("user@example.com", extra_claims={"user_id": 42, "role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "user@example.com"
    assert payload["user_id"] == 42
    assert payload["role"] == "admin"


def test_invalid_token_raises() -> None:
    with pytest.raises(ValueError):
        decode_token("not-a-real-token")
