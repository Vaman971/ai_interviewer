"""Pydantic v2 schemas for User-related requests and responses."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Request schema for user registration.

    Attributes:
        email: Valid email address.
        password: Plain-text password (8-128 chars).
        full_name: Optional display name.
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)


class UserLogin(BaseModel):
    """Request schema for user login.

    Attributes:
        email: Registered email address.
        password: Plain-text password.
    """

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema containing a JWT access token.

    Attributes:
        access_token: The JWT bearer token.
        token_type: Token type, always ``"bearer"``.
    """

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response schema for user profile data.

    Attributes:
        id: User UUID.
        email: Email address.
        full_name: Display name, if set.
        is_active: Whether the account is enabled.
        created_at: Account creation timestamp.
    """

    id: str
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
