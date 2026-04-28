"""Security utilities for hashing and JWT management."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import jwt
from passlib.context import CryptContext

# Configuration - in a real app, use a secure secret from environment
SECRET_KEY = os.getenv("JWT_SECRET", "aideator-super-secret-key-change-me-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    # Bcrypt has a 72-byte limit for the plain password
    # We truncate to 72 bytes to be safe across all bcrypt versions and passlib
    pw_bytes = plain_password.encode("utf-8")
    truncated_pw = pw_bytes[:72].decode("utf-8", errors="ignore")
    return pwd_context.verify(truncated_pw, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a hash for a plain password."""
    # Bcrypt has a 72-byte limit for the plain password
    pw_bytes = password.encode("utf-8")
    truncated_pw = pw_bytes[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(truncated_pw)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(encoded_jwt, bytes):
        return encoded_jwt.decode("utf-8")
    return cast(str, encoded_jwt)  # type: ignore[redundant-cast, unused-ignore]


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
