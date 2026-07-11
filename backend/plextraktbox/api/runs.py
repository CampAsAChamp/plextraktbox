"""Run history API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from plextraktbox.api.deps import CurrentUserDep, SessionDep
from plextraktbox.schemas.run import RunListItem, RunListResponse
from plextraktbox.services import runs as run_svc

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=RunListResponse)
def list_runs(
    _user: CurrentUserDep,
    session: SessionDep,
    job_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> RunListResponse:
    runs = run_svc.list_runs(session, job_id=job_id, limit=limit, offset=offset)
    items = [
        RunListItem.from_model(
            run,
            job_name=run_svc.resolve_job_name(session, run),
        )
        for run in runs
    ]
    return RunListResponse(items=items, limit=limit, offset=offset)


@router.get("/{run_id}", response_model=RunListItem)
def get_run(run_id: int, _user: CurrentUserDep, session: SessionDep) -> RunListItem:
    run = run_svc.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunListItem.from_model(
        run,
        job_name=run_svc.resolve_job_name(session, run),
    )
