"""
FinSight AI — API Dependencies
Shared FastAPI dependencies for authentication, authorization, and DB access.
"""

from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.models.user import User, UserRole


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from JWT token."""
    token = None

    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]

    # Fall back to cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise UnauthorizedException("Missing authentication token")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise ForbiddenException("Account is deactivated")

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Ensure the user is active."""
    if not user.is_active:
        raise ForbiddenException("Account is deactivated")
    return user


def require_role(*roles: UserRole):
    """Create a dependency that checks if user has one of the required roles."""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenException(
                f"Required role: {', '.join(r.value for r in roles)}"
            )
        return user
    return role_checker


# Type aliases for clean dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
AnalystUser = Annotated[User, Depends(require_role(UserRole.ANALYST, UserRole.ADMIN))]
DBSession = Annotated[AsyncSession, Depends(get_db)]
