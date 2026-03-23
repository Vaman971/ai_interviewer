"""SQLAlchemy ORM model for the User entity."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base

if TYPE_CHECKING:
    from backend.app.models.interview import Interview


def _utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    """Registered platform user.

    Attributes:
        id: UUID primary key.
        email: Unique email address.
        hashed_password: Bcrypt-hashed password.
        full_name: Optional display name.
        is_active: Whether the account is enabled.
        created_at: Account creation timestamp.
        updated_at: Last modification timestamp.
        interviews: Related interview sessions.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    interviews: Mapped[list[Interview]] = relationship(
        "Interview", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"<User {self.email}>"
