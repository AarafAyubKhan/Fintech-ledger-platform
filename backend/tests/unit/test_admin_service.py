"""
FinSight AI — Admin Service Unit Tests
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin_service import AdminService


@pytest.mark.asyncio
class TestAdminService:
    """Tests for the AdminService."""

    async def test_get_platform_stats(self, db_session: AsyncSession, test_user):
        """Test that platform stats returns expected keys."""
        service = AdminService(db_session)
        stats = await service.get_platform_stats()

        assert "total_users" in stats
        assert "total_documents" in stats
        assert "total_conversations" in stats
        assert "total_reports" in stats
        assert stats["total_users"] >= 1  # At least the test_user

    async def test_get_users_default(self, db_session: AsyncSession, test_user, admin_user):
        """Test listing users returns expected results."""
        service = AdminService(db_session)
        users, total = await service.get_users()

        assert total >= 2
        assert len(users) >= 2

    async def test_get_users_with_role_filter(self, db_session: AsyncSession, test_user, admin_user):
        """Test filtering users by role."""
        service = AdminService(db_session)
        users, total = await service.get_users(role="admin")

        assert total == 1
        assert users[0].email == "admin@example.com"

    async def test_get_users_with_search(self, db_session: AsyncSession, test_user):
        """Test searching users by name."""
        service = AdminService(db_session)
        users, total = await service.get_users(search="Test")

        assert total >= 1
        assert any(u.name == "Test User" for u in users)

    async def test_update_user_role(self, db_session: AsyncSession, test_user, admin_user):
        """Test updating a user's role."""
        service = AdminService(db_session)
        updated = await service.update_user_role(
            user_id=test_user.id,
            new_role="analyst",
            admin_id=admin_user.id,
        )

        assert updated.role.value == "analyst"

    async def test_update_user_role_invalid(self, db_session: AsyncSession, test_user, admin_user):
        """Test updating with invalid role raises ValueError."""
        service = AdminService(db_session)

        with pytest.raises(ValueError, match="Invalid role"):
            await service.update_user_role(
                user_id=test_user.id,
                new_role="superadmin",
                admin_id=admin_user.id,
            )

    async def test_toggle_user_active(self, db_session: AsyncSession, test_user, admin_user):
        """Test toggling user active status."""
        service = AdminService(db_session)
        assert test_user.is_active is True

        updated = await service.toggle_user_active(test_user.id, admin_user.id)
        assert updated.is_active is False

    async def test_get_audit_logs(self, db_session: AsyncSession, test_user, admin_user):
        """Test retrieving audit logs."""
        # First, create some audit log entries by performing actions
        service = AdminService(db_session)
        await service.update_user_role(test_user.id, "analyst", admin_user.id)

        logs, total = await service.get_audit_logs()
        assert total >= 1
