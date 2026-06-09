"""
FinSight AI — User Model
Supports email/password auth, Google OAuth, and RBAC.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ANALYST = "analyst"
    ADMIN = "admin"


class OAuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    oauth_provider: Mapped[OAuthProvider] = mapped_column(
        Enum(OAuthProvider), default=OAuthProvider.LOCAL, nullable=False
    )
    oauth_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversations = relationship("Conversation", back_populates="user", lazy="selectin")
    documents = relationship("Document", back_populates="uploaded_by_user", lazy="selectin")
    reports = relationship("Report", back_populates="user", lazy="selectin")
    feedback = relationship("Feedback", back_populates="user", lazy="selectin")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
