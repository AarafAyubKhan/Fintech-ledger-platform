"""
FinSight AI — Authentication Endpoints
Signup, login, Google OAuth, JWT refresh, and logout.
"""

from datetime import datetime, timezone

import httpx
import structlog
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.config import get_settings
from app.core.database import get_db
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.user import OAuthProvider, User, UserRole
from app.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Register a new user with email and password."""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise ConflictException("An account with this email already exists")

    # Create user
    user_id = str(uuid7())
    user = User(
        id=user_id,
        email=request.email,
        name=request.name,
        password_hash=hash_password(request.password),
        role=UserRole.USER,
        oauth_provider=OAuthProvider.LOCAL,
        is_active=True,
        is_verified=False,
    )
    db.add(user)

    # Audit log
    db.add(AuditLog(
        id=str(uuid7()),
        user_id=user_id,
        action="user_signup",
        resource_type="user",
        resource_id=user_id,
    ))

    await db.flush()

    tokens = create_token_pair(user.id, user.email, user.role.value)
    logger.info("user_registered", user_id=user_id, email=request.email)
    return TokenResponse(**tokens)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email and password."""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise UnauthorizedException("Invalid email or password")

    if not verify_password(request.password, user.password_hash):
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    # Audit log
    db.add(AuditLog(
        id=str(uuid7()),
        user_id=user.id,
        action="user_login",
        resource_type="user",
        resource_id=user.id,
    ))

    tokens = create_token_pair(user.id, user.email, user.role.value)

    # Set HTTP-only cookie as well
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.jwt_access_token_expire_minutes * 60,
    )

    logger.info("user_logged_in", user_id=user.id)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh an expired access token using a valid refresh token."""
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid or expired refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedException("User not found or deactivated")

    tokens = create_token_pair(user.id, user.email, user.role.value)
    return TokenResponse(**tokens)


@router.get("/google")
async def google_oauth_redirect() -> dict:
    """Initiate Google OAuth flow — returns the authorization URL."""
    if not settings.google_client_id:
        raise UnauthorizedException("Google OAuth is not configured")

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        "&response_type=code"
        "&scope=openid email profile"
        "&access_type=offline"
    )
    return {"authorization_url": auth_url}


@router.get("/google/callback", response_model=TokenResponse)
async def google_oauth_callback(
    code: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Handle Google OAuth callback — exchange code for tokens."""
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
    result = await db.execute(select(User).where(User.email == email))
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
        db.add(user)
        db.add(AuditLog(
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

    await db.flush()

    tokens = create_token_pair(user.id, user.email, user.role.value)

    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.jwt_access_token_expire_minutes * 60,
    )

    logger.info("user_oauth_login", user_id=user.id, provider="google")
    return TokenResponse(**tokens)


@router.post("/logout")
async def logout(response: Response) -> dict:
    """Clear the access token cookie."""
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}
