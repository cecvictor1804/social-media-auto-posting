"""Session-cookie authentication for the dashboard."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import User
from app.security import hash_password, verify_password


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
    """Resolve the logged-in user or raise 401.

    The SPA calls the API with the session cookie; a 401 is intercepted client
    side and routed to the login page (no server-side redirect needed).
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = session.get(User, user_id)
    if user is None or not user.is_active:
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
