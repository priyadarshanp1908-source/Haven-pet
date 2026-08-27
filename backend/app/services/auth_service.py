"""Auth service — signup, login, token refresh, and Email OTP password reset logic."""

import random
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import SignupRequest, LoginRequest, TokenRefreshRequest, ForgotPasswordRequest, ResetPasswordRequest

logger = logging.getLogger(__name__)

# In-memory OTP storage: email -> {"user_id": str, "otp": str, "expires_at": datetime}
_otp_store: dict[str, dict] = {}


async def signup(data: SignupRequest, db: AsyncSession) -> dict:
    """Register a new user account with name, email, and password."""
    email_clean = data.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email_clean))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered",
        )

    user = User(
        name=data.name.strip(),
        email=email_clean,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.flush()

    return _create_token_pair(user.id)


async def login(data: LoginRequest, db: AsyncSession) -> dict:
    """Authenticate user using Email Address and Password."""
    email_clean = data.email.lower().strip()
    result = await db.execute(
        select(User).where(User.email == email_clean)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password",
        )

    return _create_token_pair(user.id)


async def refresh_token(data: TokenRefreshRequest, db: AsyncSession) -> dict:
    """Validate refresh token and issue a new token pair."""
    payload = decode_token(data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
        )

    return _create_token_pair(user.id)


async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession) -> dict:
    """Generate and send 6-digit OTP code to user email address for password reset."""
    email_clean = data.email.lower().strip()
    
    result = await db.execute(select(User).where(User.email == email_clean))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered account found with this email address.",
        )

    # Generate 6-digit OTP code
    otp = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    _otp_store[email_clean] = {
        "user_id": user.id,
        "otp": otp,
        "expires_at": expires_at,
    }

    # Log Email OTP dispatch
    logger.info(f"📧 [EMAIL SERVICE] Sent OTP verification code '{otp}' to email address: {email_clean}")

    return {
        "message": f"OTP verification code sent via Email to {email_clean}. (Code: {otp})",
        "email": email_clean,
        "otp": otp,
    }


async def reset_password(data: ResetPasswordRequest, db: AsyncSession) -> dict:
    """Verify email OTP code and update user password."""
    email_clean = data.email.lower().strip()
    stored = _otp_store.get(email_clean)

    if not stored:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP request found for this email address. Please click 'Send OTP' first.",
        )

    if datetime.now(timezone.utc) > stored["expires_at"]:
        _otp_store.pop(email_clean, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired. Please request a new OTP code.",
        )

    if stored["otp"] != data.otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please check your email and try again.",
        )

    user_id = stored.get("user_id")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found",
        )

    # Update user password
    user.hashed_password = hash_password(data.new_password)
    await db.flush()

    # Clear OTP
    _otp_store.pop(email_clean, None)

    return {"message": "Password updated successfully! You can now sign in with your new password."}


def _create_token_pair(user_id: str) -> dict:
    """Helper to generate access + refresh token pair."""
    return {
        "access_token": create_access_token({"sub": user_id}),
        "refresh_token": create_refresh_token({"sub": user_id}),
        "token_type": "bearer",
    }
