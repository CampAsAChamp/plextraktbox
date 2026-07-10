"""FastAPI dependencies for database sessions, auth, and CSRF."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlmodel import Session, select

from plextraktbox.db import get_session
from plextraktbox.models.user import User

SessionDep = Annotated[Session, Depends(get_session)]


def require_csrf(x_requested_with: str | None = Header(default=None)) -> None:
    """Reject mutating requests that do not identify as same-origin XHR."""
    if x_requested_with != "XMLHttpRequest":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing or invalid X-Requested-With header",
        )


def user_exists(session: Session) -> bool:
    return session.exec(select(User).limit(1)).first() is not None


def get_current_user(request: Request, session: SessionDep) -> User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = session.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
