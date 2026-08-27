"""Auth routes — signup, login, token refresh."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, TokenRefreshRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserOut
from app.services import auth_service
from app.models.user import User

router = APIRouter()


@router.post("/auth/signup", response_model=TokenResponse, status_code=201)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    return await auth_service.signup(data, db)


@router.post("/auth/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive access + refresh tokens."""
    return await auth_service.login(data, db)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an expired access token using a valid refresh token."""
    return await auth_service.refresh_token(data, db)


@router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request an OTP code to be sent to user email for password reset."""
    return await auth_service.forgot_password(data, db)


@router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP code and set new user password."""
    return await auth_service.reset_password(data, db)


@router.get("/auth/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return current_user
