"""Session-based login, logout, and current-user endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import or_, select

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.models.user import User
from plextraktbox.schemas.auth import LoginRequest, UserResponse
from plextraktbox.security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse, dependencies=[Depends(require_csrf)])
def login(body: LoginRequest, request: Request, session: SessionDep) -> UserResponse:
    statement = select(User).where(
        or_(User.username == body.username, User.email == body.username),
    )
    user = session.exec(statement).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    request.session["user_id"] = user.id
    return UserResponse.from_user(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def logout(request: Request, _user: CurrentUserDep) -> None:
    request.session.clear()


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUserDep) -> UserResponse:
    return UserResponse.from_user(user)
