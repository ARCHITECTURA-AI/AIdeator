"""Authentication router for AIdeator."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from api.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from db.users import get_user_by_email, save_user
from models.user import User

LOGGER = logging.getLogger("api.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


async def get_current_user(token: Annotated[str | None, Depends(oauth2_scheme)] = None) -> User:
    """Dependency to get the currently authenticated user."""
    import os
    bypass = os.environ.get("IDEATOR_TEST_BYPASS")
    strict = os.environ.get("IDEATOR_STRICT_AUTH")
    if bypass == "true" and strict != "true":
        # Return a system user for legacy tests
        return User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="mock"
        )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception

    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration) -> dict[str, str]:
    """Register a new user."""
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
    )
    save_user(user)

    LOGGER.info(f"User registered: {user.email}")
    return {"message": "User registered successfully", "user_id": str(user.user_id)}


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Authenticate a user and return a JWT token."""
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    LOGGER.info(f"User logged in: {user.email}")
    return Token(access_token=access_token, token_type="bearer")
