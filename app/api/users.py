"""User management API — admin-only."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.deps import DBSession, RequireAdmin
from app.models import User
from app.schemas import CreateUserIn, UpdateUserIn, UserAdminOut
from app.security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserAdminOut])
def list_users(admin: RequireAdmin, session: DBSession):
    users = list(session.scalars(select(User).order_by(User.created_at)))
    return [UserAdminOut.from_orm_user(u) for u in users]


@router.post("", response_model=UserAdminOut, status_code=201)
def create_user(payload: CreateUserIn, admin: RequireAdmin, session: DBSession):
    email = payload.email.strip().lower()
    if session.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserAdminOut.from_orm_user(user)


@router.patch("/{user_id}", response_model=UserAdminOut)
def update_user(user_id: int, payload: UpdateUserIn, admin: RequireAdmin, session: DBSession):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.is_admin is False and user.is_admin:
        admin_count = session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.is_admin.is_(True), User.is_active.is_(True))
        )
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last admin")
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    if payload.is_active is not None:
        user.is_active = payload.is_active
    session.commit()
    session.refresh(user)
    return UserAdminOut.from_orm_user(user)
