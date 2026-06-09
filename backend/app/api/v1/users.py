"""
FinSight AI — User Management Endpoints
Profile management and user queries.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBSession
from app.core.database import get_db
from app.models.user import User
from app.schemas import UserResponse, UserUpdateRequest

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: CurrentUser) -> UserResponse:
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    request: UserUpdateRequest,
    user: CurrentUser,
    db: DBSession,
) -> UserResponse:
    """Update the current user's profile."""
    if request.name is not None:
        user.name = request.name
    if request.avatar_url is not None:
        user.avatar_url = request.avatar_url

    await db.flush()
    return UserResponse.model_validate(user)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: DBSession,
    skip: int = 0,
    limit: int = 50,
) -> list[UserResponse]:
    """List all users (for admin panel consumption)."""
    result = await db.execute(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]
