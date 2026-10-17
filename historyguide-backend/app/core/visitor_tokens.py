import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time


def issue_visitor_token(session_id: str, signing_key: str, ttl_minutes: int) -> tuple[str, int]:
    expires_at = int(time.time()) + ttl_minutes * 60
    payload = {
        "v": 1,
        "sid": session_id,
        "exp": expires_at,
        "nonce": secrets.token_urlsafe(12),
    }
    body = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    signature = _encode(hmac.new(signing_key.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{signature}", expires_at


def verify_visitor_token(token: str, signing_key: str) -> str | None:
    if len(token) > 1024 or token.count(".") != 1:
        return None
    body, signature = token.split(".", 1)
    try:
        supplied_signature = _decode(signature)
        expected_signature = hmac.new(
            signing_key.encode("utf-8"), body.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return None
        payload = json.loads(_decode(body))
    except (ValueError, UnicodeError, TypeError, binascii.Error):
        return None
    if not isinstance(payload, dict) or payload.get("v") != 1:
        return None
    session_id = payload.get("sid")
    expiry = payload.get("exp")
    if not isinstance(session_id, str) or not 1 <= len(session_id) <= 64:
        return None
    if type(expiry) is not int or expiry <= int(time.time()):
        return None
    return session_id


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
