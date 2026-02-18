from __future__ import annotations

import hashlib
import secrets


def hash_password(password: str, salt: str | None = None) -> str:
    s = salt or secrets.token_hex(16)
    digest = hashlib.sha256(f"{s}:{password}".encode()).hexdigest()
    return f"{s}${digest}"


def verify_password(password: str, hashed: str) -> bool:
    salt, _ = hashed.split("$", 1)
    return hash_password(password, salt) == hashed


def new_token() -> str:
    return secrets.token_urlsafe(32)
