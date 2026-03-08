from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import secrets
from typing import Any

try:
    from jose import JWTError, jwt
except ImportError:  # pragma: no cover - fallback path used in stripped envs
    JWTError = Exception  # type: ignore[assignment]
    jwt = None

try:
    from passlib.context import CryptContext
except ImportError:  # pragma: no cover - fallback path used in stripped envs
    CryptContext = None  # type: ignore[assignment]

from app.config import Settings, get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext else None


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def hash_password(password: str) -> str:
    if pwd_context:
        return pwd_context.hash(password)
    salt = secrets.token_hex(16)
    rounds = 600_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), rounds)
    return f"pbkdf2_sha256${rounds}${salt}${digest.hex()}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    if pwd_context:
        return pwd_context.verify(plain_password, password_hash)
    try:
        algorithm, rounds_raw, salt, expected_hex = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(rounds_raw)
        digest = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), rounds
        )
        return hmac.compare_digest(digest.hex(), expected_hex)
    except ValueError:
        return False


def create_access_token(
    subject: str,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> str:
    cfg = settings or get_settings()
    expire_minutes = expires_minutes or cfg.access_token_expire_minutes
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire_at}
    if extra_claims:
        payload.update(extra_claims)
    if jwt:
        return jwt.encode(payload, cfg.app_secret_key, algorithm=cfg.jwt_algorithm)

    # Fallback signer for environments where jwt libs are unavailable.
    fallback_payload = dict(payload)
    fallback_payload["exp"] = int(expire_at.timestamp())
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(
        json.dumps(fallback_payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(
        cfg.app_secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"


def decode_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    if jwt:
        try:
            return jwt.decode(token, cfg.app_secret_key, algorithms=[cfg.jwt_algorithm])
        except JWTError as exc:
            raise ValueError("Invalid token") from exc

    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".", 2)
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_signature = hmac.new(
            cfg.app_secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected_signature, _b64url_decode(encoded_signature)):
            raise ValueError("Invalid token signature")
        payload = json.loads(_b64url_decode(encoded_payload))
        exp = int(payload.get("exp", 0))
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise ValueError("Token expired")
        return payload
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid token") from exc
