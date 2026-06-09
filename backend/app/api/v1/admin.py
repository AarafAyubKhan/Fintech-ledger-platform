"""
FinSight AI — Admin Endpoints
User management, analytics, and system configuration.
"""

from datetime import datetime, timezone, timedelta

import structlog
from fastapi import APIRouter
from sqlalchemy import select, func, and_
from uuid6 import uuid7

from app.api.deps import AdminUser, DBSession
from app.core.exceptions import NotFoundException
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.document import Document, DocumentStatus
from app.models.report import Report
from app.models.user import User, UserRole
from app.schemas import (
    AdminStatsResponse,
    AuditLogResponse,
    UserResponse,
    UserRoleUpdateRequest,
)

router = APIRouter()
logger = structlog.get_logger()


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin: AdminUser,
    db: DBSession,
) -> AdminStatsResponse:
    """Get platform-wide usage statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_documents = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    total_conversations = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    total_reports = (await db.execute(select(func.count(Report.id)))).scalar() or 0

    active_today = (
        await db.execute(
            select(func.count(User.id)).where(User.last_login >= today_start)
        )
    ).scalar() or 0

    docs_processed = (
        await db.execute(
            select(func.count(Document.id)).where(
                Document.status == DocumentStatus.COMPLETED
            )
        )
    ).scalar() or 0

    return AdminStatsResponse(
        total_users=total_users,
        total_documents=total_documents,
        total_conversations=total_conversations,
        total_reports=total_reports,
        active_users_today=active_today,
        documents_processed=docs_processed,
        avg_response_time_ms=0.0,
    )


@router.get("/users", response_model=list[UserResponse])
async def admin_list_users(
    admin: AdminUser,
    db: DBSession,
    skip: int = 0,
    limit: int = 50,
    role: str | None = None,
) -> list[UserResponse]:
    """List all users with optional role filter."""
    query = select(User)
    if role:
        query = query.where(User.role == role)

    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    request: UserRoleUpdateRequest,
    admin: AdminUser,
    db: DBSession,
) -> UserResponse:
    """Update a user's role (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", user_id)

    user.role = UserRole(request.role)

    # Audit log
    db.add(AuditLog(
        id=str(uuid7()),
        user_id=admin.id,
        action="user_role_updated",
        resource_type="user",
        resource_id=user_id,
        details={"new_role": request.role},
    ))

    await db.flush()
    logger.info("user_role_updated", user_id=user_id, new_role=request.role, by=admin.id)
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: str,
    admin: AdminUser,
    db: DBSession,
) -> UserResponse:
    """Activate or deactivate a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", user_id)

    user.is_active = not user.is_active

    db.add(AuditLog(
        id=str(uuid7()),
        user_id=admin.id,
        action="user_toggled_active",
        resource_type="user",
        resource_id=user_id,
        details={"is_active": user.is_active},
    ))

    await db.flush()
    return UserResponse.model_validate(user)


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    admin: AdminUser,
    db: DBSession,
    skip: int = 0,
    limit: int = 100,
    action: str | None = None,
    user_id: str | None = None,
) -> list[AuditLogResponse]:
    """Retrieve audit logs with optional filtering."""
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return [AuditLogResponse.model_validate(log) for log in result.scalars().all()]
