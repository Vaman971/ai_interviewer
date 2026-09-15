"""Authentication API routes: register, login, and profile retrieval."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.db.redis import get_redis
from backend.app.models.user import User
from backend.app.schemas.user import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from backend.app.services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    revoke_token,
    oauth2_scheme,
)

async def check_rate_limit(request: Request, action: str, limit: int = 10, window: int = 60) -> None:
    """Rate limit requests using Redis sliding window counter."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{action}:{client_ip}"
    try:
        r = await get_redis()
        attempts = await r.incr(key)
        if attempts == 1:
            await r.expire(key, window)
        if attempts > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Redis unavailable, fail open

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user account.

    Args:
        request: The incoming HTTP request (for rate limiting).
        data: Registration payload with email, password, and optional name.
        db: Async database session.

    Returns:
        The newly created user record.

    Raises:
        HTTPException: If the email is already registered.
    """
    await check_rate_limit(request, action="register", limit=10, window=60)

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_count_q = await db.execute(select(func.count()).select_from(User))
    user_count = user_count_q.scalar() or 0
    is_first_user = (user_count == 0)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_admin=is_first_user,
        is_super_admin=is_first_user,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate a user and return a JWT access token.

    Args:
        request: The incoming HTTP request (for rate limiting).
        data: Login payload with email and password.
        db: Async database session.

    Returns:
        Dictionary with ``access_token`` and ``token_type``.

    Raises:
        HTTPException: If the credentials are invalid.
    """
    await check_rate_limit(request, action="login", limit=10, window=60)

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile.

    Args:
        current_user: The user extracted from the JWT bearer token.

    Returns:
        The current user record.
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(token: str = Depends(oauth2_scheme)) -> None:
    """Log out the current user by revoking their token.

    Adds the JWT token to the Redis blocklist.

    Args:
        token: The current user's JWT bearer token.
    """
    await revoke_token(token)
    return None
