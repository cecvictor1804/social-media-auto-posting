"""Auth routes: cookie login/logout + current-user probe."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.api.deps import CurrentUser, DBSession
from app.auth import authenticate
from app.schemas import LoginIn, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, request: Request, session: DBSession):
    user = authenticate(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    request.session["user_id"] = user.id
    return UserOut(id=user.id, email=user.email, is_admin=user.is_admin)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return UserOut(id=user.id, email=user.email, is_admin=user.is_admin)
