"""
FinSight AI — Admin Service
Business logic for platform administration, statistics, and user management.
"""

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.document import Document, DocumentStatus
from app.models.report import Report
from app.models.user import User, UserRole

logger = structlog.get_logger()


class AdminService:
    """Handles platform administration, statistics, and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_platform_stats(self) -> dict:
        """Aggregate platform-wide statistics for the admin dashboard."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Total counts
        total_users = (await self.db.execute(
            select(func.count()).select_from(User)
        )).scalar() or 0

        total_documents = (await self.db.execute(
            select(func.count()).select_from(Document)
        )).scalar() or 0

        total_conversations = (await self.db.execute(
            select(func.count()).select_from(Conversation)
        )).scalar() or 0

        total_reports = (await self.db.execute(
            select(func.count()).select_from(Report)
        )).scalar() or 0

        # Active users today (logged in today)
        active_users_today = (await self.db.execute(
            select(func.count()).select_from(User).where(
                User.last_login >= today_start
            )
        )).scalar() or 0

        # Documents processed
        documents_processed = (await self.db.execute(
            select(func.count()).select_from(Document).where(
                Document.status == DocumentStatus.COMPLETED
            )
        )).scalar() or 0

        # Average response time (from recent conversations, mocked if no data)
        avg_response_time_ms = 0.0

        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_conversations": total_conversations,
            "total_reports": total_reports,
            "active_users_today": active_users_today,
            "documents_processed": documents_processed,
            "avg_response_time_ms": avg_response_time_ms,
        }

    async def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: str | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """List all users with filtering and pagination.
        
        Returns:
            Tuple of (user_list, total_count).
        """
        query = select(User)

        if role:
            try:
                user_role = UserRole(role)
                query = query.where(User.role == user_role)
            except ValueError:
                pass

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (User.name.ilike(search_filter)) | (User.email.ilike(search_filter))
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total

    async def update_user_role(self, user_id: str, new_role: str, admin_id: str) -> User:
        """Update a user's role.
        
        Raises:
            ValueError: If user not found or role is invalid.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        try:
            role = UserRole(new_role)
        except ValueError:
            raise ValueError(f"Invalid role: {new_role}")

        old_role = user.role.value
        user.role = role

        # Audit log
        from uuid6 import uuid7
        self.db.add(AuditLog(
            id=str(uuid7()),
            user_id=admin_id,
            action="user_role_changed",
            resource_type="user",
            resource_id=user_id,
            details={"old_role": old_role, "new_role": new_role},
        ))

        logger.info(
            "user_role_updated",
            user_id=user_id,
            old_role=old_role,
            new_role=new_role,
            admin_id=admin_id,
        )

        return user

    async def toggle_user_active(self, user_id: str, admin_id: str) -> User:
        """Activate or deactivate a user account.
        
        Raises:
            ValueError: If user not found.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        user.is_active = not user.is_active

        from uuid6 import uuid7
        self.db.add(AuditLog(
            id=str(uuid7()),
            user_id=admin_id,
            action="user_deactivated" if not user.is_active else "user_activated",
            resource_type="user",
            resource_id=user_id,
        ))

        logger.info("user_active_toggled", user_id=user_id, is_active=user.is_active)
        return user

    async def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        user_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        """Retrieve audit logs with filtering and pagination.
        
        Returns:
            Tuple of (audit_log_list, total_count).
        """
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(AuditLog.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total

    async def get_usage_trends(self, days: int = 30) -> dict:
        """Get platform usage trends for the past N days."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        # Daily new users
        daily_users = await self.db.execute(
            select(
                func.date_trunc("day", User.created_at).label("day"),
                func.count().label("count"),
            )
            .where(User.created_at >= start)
            .group_by("day")
            .order_by("day")
        )

        # Daily documents uploaded
        daily_docs = await self.db.execute(
            select(
                func.date_trunc("day", Document.created_at).label("day"),
                func.count().label("count"),
            )
            .where(Document.created_at >= start)
            .group_by("day")
            .order_by("day")
        )

        # Daily reports generated
        daily_reports = await self.db.execute(
            select(
                func.date_trunc("day", Report.created_at).label("day"),
                func.count().label("count"),
            )
            .where(Report.created_at >= start)
            .group_by("day")
            .order_by("day")
        )

        return {
            "daily_users": [
                {"date": row.day.isoformat(), "count": row.count}
                for row in daily_users
            ],
            "daily_documents": [
                {"date": row.day.isoformat(), "count": row.count}
                for row in daily_docs
            ],
            "daily_reports": [
                {"date": row.day.isoformat(), "count": row.count}
                for row in daily_reports
            ],
        }
