"""
FinSight AI — Auth Service
Business logic for user authentication, registration, and token management.
"""

from datetime import datetime, timezone

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.config import get_settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.user import OAuthProvider, User, UserRole

logger = structlog.get_logger()
settings = get_settings()


class AuthService:
    """Handles user authentication, registration, and OAuth flows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str, name: str) -> tuple[User, dict[str, str]]:
        """Register a new user with email and password.
        
        Returns:
            Tuple of (User, token_pair dict).
        
        Raises:
            ConflictException: If user with email already exists.
        """
        # Check for existing user
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ConflictException("An account with this email already exists")

        user_id = str(uuid7())
        user = User(
            id=user_id,
            email=email,
            name=name,
            password_hash=hash_password(password),
            role=UserRole.USER,
            oauth_provider=OAuthProvider.LOCAL,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)

        # Audit log
        self.db.add(AuditLog(
            id=str(uuid7()),
            user_id=user_id,
            action="user_signup",
            resource_type="user",
            resource_id=user_id,
        ))

        await self.db.flush()

        tokens = create_token_pair(user.id, user.email, user.role.value)
        logger.info("user_registered", user_id=user_id, email=email)
        return user, tokens

    async def login(self, email: str, password: str) -> tuple[User, dict[str, str]]:
        """Authenticate a user with email and password.
        
        Returns:
            Tuple of (User, token_pair dict).
        
        Raises:
            UnauthorizedException: If credentials are invalid.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        # Update last login
        user.last_login = datetime.now(timezone.utc)

        # Audit log
        self.db.add(AuditLog(
            id=str(uuid7()),
            user_id=user.id,
            action="user_login",
            resource_type="user",
            resource_id=user.id,
        ))

        tokens = create_token_pair(user.id, user.email, user.role.value)
        logger.info("user_logged_in", user_id=user.id)
        return user, tokens

    async def refresh_tokens(self, refresh_token: str) -> dict[str, str]:
        """Exchange a refresh token for a new token pair.
        
        Raises:
            UnauthorizedException: If refresh token is invalid or expired.
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid or expired refresh token")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException("User not found or deactivated")

        return create_token_pair(user.id, user.email, user.role.value)

    async def google_oauth_exchange(self, code: str) -> tuple[User, dict[str, str]]:
        """Handle Google OAuth callback — exchange code for user + tokens.
        
        Returns:
            Tuple of (User, token_pair dict).
        
        Raises:
            UnauthorizedException: If OAuth exchange fails.
        """
        if not settings.google_client_id:
            raise UnauthorizedException("Google OAuth is not configured")

        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_response.status_code != 200:
                raise UnauthorizedException("Failed to exchange OAuth code")

            token_data = token_response.json()
            google_access_token = token_data.get("access_token")

            # Get user info from Google
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"},
            )
            if userinfo_response.status_code != 200:
                raise UnauthorizedException("Failed to fetch Google user info")

            userinfo = userinfo_response.json()

        google_id = userinfo.get("id")
        email = userinfo.get("email")
        name = userinfo.get("name", email)
        avatar = userinfo.get("picture")

        # Find or create user
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=str(uuid7()),
                email=email,
                name=name,
                oauth_provider=OAuthProvider.GOOGLE,
                oauth_id=google_id,
                avatar_url=avatar,
                role=UserRole.USER,
                is_active=True,
                is_verified=True,
            )
            self.db.add(user)
            self.db.add(AuditLog(
                id=str(uuid7()),
                user_id=user.id,
                action="user_oauth_signup",
                resource_type="user",
                resource_id=user.id,
                details={"provider": "google"},
            ))
        else:
            user.last_login = datetime.now(timezone.utc)
            user.avatar_url = avatar or user.avatar_url

        await self.db.flush()

        tokens = create_token_pair(user.id, user.email, user.role.value)
        logger.info("user_oauth_login", user_id=user.id, provider="google")
        return user, tokens

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Fetch a user by their ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        """Update user's password after verifying current password.
        
        Raises:
            UnauthorizedException: If current password doesn't match.
        """
        if user.password_hash and not verify_password(current_password, user.password_hash):
            raise UnauthorizedException("Current password is incorrect")

        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)

        self.db.add(AuditLog(
            id=str(uuid7()),
            user_id=user.id,
            action="password_changed",
            resource_type="user",
            resource_id=user.id,
        ))

        logger.info("password_changed", user_id=user.id)
