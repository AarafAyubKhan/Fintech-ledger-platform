"""
FinSight AI — Auth Service Unit Tests
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import verify_password
from app.services.auth_service import AuthService


@pytest.mark.asyncio
class TestAuthService:
    """Tests for the AuthService."""

    async def test_register_creates_user(self, db_session: AsyncSession):
        """Test successful user registration."""
        service = AuthService(db_session)
        user, tokens = await service.register(
            email="new@example.com",
            password="StrongPass123",
            name="New User",
        )

        assert user.email == "new@example.com"
        assert user.name == "New User"
        assert user.is_active is True
        assert tokens["access_token"]
        assert tokens["refresh_token"]
        assert tokens["token_type"] == "bearer"

    async def test_register_duplicate_email_raises(self, db_session: AsyncSession, test_user):
        """Test that registering with an existing email raises ConflictException."""
        service = AuthService(db_session)

        with pytest.raises(ConflictException):
            await service.register(
                email=test_user.email,
                password="AnotherPass123",
                name="Another User",
            )

    async def test_login_with_valid_credentials(self, db_session: AsyncSession, test_user):
        """Test successful login with valid email/password."""
        service = AuthService(db_session)
        user, tokens = await service.login(
            email="testuser@example.com",
            password="TestPass123",
        )

        assert user.id == test_user.id
        assert tokens["access_token"]
        assert tokens["refresh_token"]

    async def test_login_with_wrong_password(self, db_session: AsyncSession, test_user):
        """Test login with wrong password raises UnauthorizedException."""
        service = AuthService(db_session)

        with pytest.raises(UnauthorizedException):
            await service.login(
                email="testuser@example.com",
                password="WrongPassword123",
            )

    async def test_login_with_nonexistent_email(self, db_session: AsyncSession):
        """Test login with nonexistent email raises UnauthorizedException."""
        service = AuthService(db_session)

        with pytest.raises(UnauthorizedException):
            await service.login(
                email="nonexistent@example.com",
                password="AnyPass123",
            )

    async def test_refresh_tokens(self, db_session: AsyncSession, test_user):
        """Test refreshing tokens with a valid refresh token."""
        service = AuthService(db_session)
        _, tokens = await service.login(
            email="testuser@example.com",
            password="TestPass123",
        )

        new_tokens = await service.refresh_tokens(tokens["refresh_token"])
        assert new_tokens["access_token"]
        assert new_tokens["access_token"] != tokens["access_token"]

    async def test_refresh_with_invalid_token(self, db_session: AsyncSession):
        """Test that refreshing with an invalid token raises."""
        service = AuthService(db_session)

        with pytest.raises(UnauthorizedException):
            await service.refresh_tokens("invalid-token")

    async def test_update_password(self, db_session: AsyncSession, test_user):
        """Test password update with valid current password."""
        service = AuthService(db_session)
        await service.update_password(
            user=test_user,
            current_password="TestPass123",
            new_password="NewPass456",
        )

        assert verify_password("NewPass456", test_user.password_hash)

    async def test_update_password_wrong_current(self, db_session: AsyncSession, test_user):
        """Test password update with wrong current password raises."""
        service = AuthService(db_session)

        with pytest.raises(UnauthorizedException):
            await service.update_password(
                user=test_user,
                current_password="WrongPass",
                new_password="NewPass456",
            )
