"""Mobile auth endpoint: exchange email+password for a JWT Bearer token."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import authenticate, create_access_token
from app.db import get_session
from app.schemas import UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/token", response_model=TokenOut)
def issue_token(payload: TokenIn, session: Session = Depends(get_session)):
    """Issue a JWT for mobile clients.  Equivalent to /api/auth/login but
    returns a Bearer token instead of setting a session cookie.
    """
    user = authenticate(session, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(user.id)
    return TokenOut(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, is_admin=user.is_admin),
    )
