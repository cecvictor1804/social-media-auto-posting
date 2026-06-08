"""Shared FastAPI dependencies used across API routers.

``CurrentUser`` enforces auth (raises 401 if not logged in); ``DBSession``
provides a request-scoped SQLAlchemy session. Using Annotated aliases removes the
repeated ``Depends(...)`` boilerplate from every route signature.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_session
from app.models import User

CurrentUser = Annotated[User, Depends(current_user)]
DBSession = Annotated[Session, Depends(get_session)]
