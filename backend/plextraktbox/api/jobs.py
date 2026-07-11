"""Job CRUD and manual run endpoints (Phase 3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.models.job_run import RunTrigger
from plextraktbox.schemas.job import JobCreateRequest, JobResponse, JobRunRequest, JobRunResponse
from plextraktbox.services import jobs as job_svc
from plextraktbox.services.sync_run import execute_job_sync

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
def list_jobs(_user: CurrentUserDep, session: SessionDep) -> list[JobResponse]:
    return [JobResponse.from_model(job) for job in job_svc.list_jobs(session)]


@router.post("", response_model=JobResponse, dependencies=[Depends(require_csrf)])
def create_job(
    body: JobCreateRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> JobResponse:
    try:
        job = job_svc.create_job(
            session,
            name=body.name,
            source_pair=body.source_pair,
            enabled=body.enabled,
            cron=body.cron,
            dry_run=body.dry_run,
            data_types=set(body.data_types),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JobResponse.from_model(job)


@router.post(
    "/{job_id}/run",
    response_model=JobRunResponse,
    dependencies=[Depends(require_csrf)],
)
def run_job(
    job_id: int,
    _user: CurrentUserDep,
    session: SessionDep,
    body: JobRunRequest | None = None,
) -> JobRunResponse:
    job = job_svc.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    dry_run_override = body.dry_run if body is not None else None
    try:
        run = execute_job_sync(
            session,
            job,
            trigger=RunTrigger.MANUAL,
            dry_run_override=dry_run_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return JobRunResponse.from_model(run)
