"""Session-cookie and Bearer-token authentication for the dashboard.

Web SPA: authenticates via HTTP-only session cookie (set by POST /api/auth/login).
Mobile app: authenticates via JWT Bearer token (issued by POST /api/auth/token).
Both paths share the same current_user dependency — web behavior is unchanged.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import User
from app.security import hash_password, verify_password


def create_access_token(user_id: int) -> str:
    """Sign a JWT for mobile clients (stored in SecureStore, sent as Bearer)."""
    exp = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    return jwt.encode(
        {"sub": str(user_id), "exp": exp},
        settings.session_secret,
        algorithm=settings.jwt_algorithm,
    )


def _decode_jwt(token: str) -> int:
    """Decode a Bearer token and return user_id, or raise 401."""
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def ensure_admin(session: Session) -> None:
    """Create the bootstrap admin user if there are no users yet."""
    exists = session.scalar(select(User).limit(1))
    if exists is None:
        session.add(
            User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                is_admin=True,
            )
        )
        session.commit()


def authenticate(session: Session, email: str, password: str) -> User | None:
    user = session.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
    if user and verify_password(password, user.password_hash):
        return user
    return None


def current_user(request: Request, session: Session = Depends(get_session)) -> User:
    """Resolve the logged-in user from either Bearer token (mobile) or session cookie (web).

    Mobile: Authorization: Bearer <jwt>  →  decode JWT to get user_id
    Web SPA: session cookie              →  read user_id from Starlette session
    Both paths resolve to the same User object; behaviour is unchanged for the web.
    """
    user_id: int | None = None

    # 1. Bearer token (mobile / React Native)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        user_id = _decode_jwt(auth_header[7:])
    else:
        # 2. Session cookie (web SPA — original behaviour)
        raw = request.session.get("user_id")
        if raw:
            user_id = int(raw)

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        if not auth_header.startswith("Bearer "):
            request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    """Dependency: authenticated + is_admin, else 403."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
