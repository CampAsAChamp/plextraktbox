"""Job CRUD and manual run endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.cron import compute_next_run_times
from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.scheduler import get_scheduler_manager
from plextraktbox.schemas.job import (
    JobCreateRequest,
    JobResponse,
    JobRunRequest,
    JobRunResponse,
    JobUpdateRequest,
    SchedulePreviewRequest,
    SchedulePreviewResponse,
)
from plextraktbox.services import jobs as job_svc

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _next_run_at(job: Job) -> datetime | None:
    """Next fire time for an enabled job (scheduler first, cron fallback)."""
    if not job.enabled or job.id is None:
        return None
    scheduled = get_scheduler_manager().get_next_run_time(job.id)
    if scheduled is not None:
        return scheduled
    # Fallback when the job is not registered in APScheduler yet (or was
    # dropped). Matches the schedule-preview endpoint so list tooltips still work.
    times = compute_next_run_times(job.cron, count=1)
    return times[0] if times else None


def _job_response(job: Job) -> JobResponse:
    return JobResponse.from_model(job, next_run_at=_next_run_at(job))


@router.get("", response_model=list[JobResponse])
def list_jobs(_user: CurrentUserDep, session: SessionDep) -> list[JobResponse]:
    return [_job_response(job) for job in job_svc.list_jobs(session)]


@router.post("/schedule-preview", response_model=SchedulePreviewResponse)
def preview_schedule(
    body: SchedulePreviewRequest,
    _user: CurrentUserDep,
) -> SchedulePreviewResponse:
    """Return the next N fire times for a draft cron expression (UTC)."""
    return SchedulePreviewResponse(times=compute_next_run_times(body.cron, count=body.count))


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, _user: CurrentUserDep, session: SessionDep) -> JobResponse:
    job = job_svc.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _job_response(job)


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
            notify_mode=body.notify_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _job_response(job)


@router.put("/{job_id}", response_model=JobResponse, dependencies=[Depends(require_csrf)])
def update_job(
    job_id: int,
    body: JobUpdateRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> JobResponse:
    job = job_svc.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    try:
        job = job_svc.update_job(
            session,
            job,
            name=body.name,
            source_pair=body.source_pair,
            enabled=body.enabled,
            cron=body.cron,
            dry_run=body.dry_run,
            data_types=set(body.data_types),
            notify_mode=body.notify_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _job_response(job)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def delete_job(job_id: int, _user: CurrentUserDep, session: SessionDep) -> None:
    job = job_svc.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job_svc.delete_job(session, job)


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

    from plextraktbox.services.preflight import validate_job_connections

    try:
        validate_job_connections(session, job)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    dry_run_override = body.dry_run if body is not None else None
    dry_run = job.dry_run if dry_run_override is None else dry_run_override

    run = JobRun(job_id=job_id, job_name=job.name, trigger=RunTrigger.MANUAL, dry_run=dry_run)
    session.add(run)
    session.commit()
    session.refresh(run)

    try:
        run = get_scheduler_manager().trigger_now(
            job_id,
            dry_run_override=dry_run_override,
            run=run,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        session.refresh(run)
        if run.status == JobRunStatus.RUNNING:
            run.status = JobRunStatus.FAILED
            run.error = str(exc)
            session.add(run)
            session.commit()
            session.refresh(run)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return JobRunResponse.from_model(run)
