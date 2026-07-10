"""First-run setup endpoints (disabled once a user exists)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from plextraktbox.api.deps import SessionDep, require_csrf, user_exists
from plextraktbox.models.user import User
from plextraktbox.schemas.auth import SetupStatusResponse, SetupUserRequest, UserResponse
from plextraktbox.security import hash_password

router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatusResponse)
def setup_status(session: SessionDep) -> SetupStatusResponse:
    return SetupStatusResponse(needs_setup=not user_exists(session))


@router.post(
    "/user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def setup_user(body: SetupUserRequest, session: SessionDep) -> UserResponse:
    if user_exists(session):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Setup already completed",
        )

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse.from_user(user)
