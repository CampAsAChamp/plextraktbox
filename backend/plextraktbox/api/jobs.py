"""Job CRUD and manual run endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.cron import compute_next_run_times
from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.scheduler import get_scheduler_manager
from plextraktbox.schemas.job import (
    JobCreateRequest,
    JobLastRun,
    JobResponse,
    JobRunRequest,
    JobRunResponse,
    JobUpdateRequest,
    SchedulePreviewRequest,
    SchedulePreviewResponse,
    exclude_ids_from_request,
)
from plextraktbox.schemas.settings import ExcludeIds
from plextraktbox.services import jobs as job_svc
from plextraktbox.services import runs as run_svc
from plextraktbox.services import settings as settings_svc
from plextraktbox.services.dry_run import resolve_dry_run

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _next_run_at(
    job: Job,
    *,
    cron_timezone: str,
    cron_local_zone: str | None,
) -> datetime | None:
    """Next fire time for an enabled job (scheduler first, cron fallback)."""
    if not job.enabled or job.id is None:
        return None
    scheduled = get_scheduler_manager().get_next_run_time(job.id)
    if scheduled is not None:
        return scheduled
    # Fallback when the job is not registered in APScheduler yet (or was
    # dropped). Matches the schedule-preview endpoint so list tooltips still work.
    times = compute_next_run_times(
        job.cron,
        count=1,
        timezone=cron_timezone,
        local_zone=cron_local_zone,
    )
    return times[0] if times else None


def _job_response(
    job: Job,
    *,
    cron_timezone: str,
    cron_local_zone: str | None,
    last_run: JobLastRun | None = None,
) -> JobResponse:
    return JobResponse.from_model(
        job,
        next_run_at=_next_run_at(
            job,
            cron_timezone=cron_timezone,
            cron_local_zone=cron_local_zone,
        ),
        last_run=last_run,
    )


def _last_run_for(session: Session, job: Job) -> JobLastRun | None:
    if job.id is None:
        return None
    latest = run_svc.latest_runs_by_job_ids(session, [job.id]).get(job.id)
    return JobLastRun.from_model(latest) if latest is not None else None


@router.get("", response_model=list[JobResponse])
def list_jobs(_user: CurrentUserDep, session: SessionDep) -> list[JobResponse]:
    app_settings = settings_svc.get_app_settings(session)
    jobs = job_svc.list_jobs(session)
    latest_by_job = run_svc.latest_runs_by_job_ids(
        session,
        [job.id for job in jobs if job.id is not None],
    )
    return [
        _job_response(
            job,
            cron_timezone=app_settings.cron_timezone,
            cron_local_zone=app_settings.cron_local_zone,
            last_run=(
                JobLastRun.from_model(latest_by_job[job.id])
                if job.id is not None and job.id in latest_by_job
                else None
            ),
        )
        for job in jobs
    ]


@router.post("/schedule-preview", response_model=SchedulePreviewResponse)
def preview_schedule(
    body: SchedulePreviewRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> SchedulePreviewResponse:
    """Return the next N fire times for a draft cron (in configured cron timezone)."""
    app_settings = settings_svc.get_app_settings(session)
    return SchedulePreviewResponse(
        times=compute_next_run_times(
            body.cron,
            count=body.count,
            timezone=app_settings.cron_timezone,
            local_zone=app_settings.cron_local_zone,
        )
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, _user: CurrentUserDep, session: SessionDep) -> JobResponse:
    job = job_svc.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    app_settings = settings_svc.get_app_settings(session)
    return _job_response(
        job,
        cron_timezone=app_settings.cron_timezone,
        cron_local_zone=app_settings.cron_local_zone,
        last_run=_last_run_for(session, job),
    )


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
            require_dry_run_first=body.require_dry_run_first,
            exclude_ids=exclude_ids_from_request(body.exclude_ids),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    app_settings = settings_svc.get_app_settings(session)
    return _job_response(
        job,
        cron_timezone=app_settings.cron_timezone,
        cron_local_zone=app_settings.cron_local_zone,
        last_run=None,
    )


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
            require_dry_run_first=body.require_dry_run_first,
            exclude_ids=exclude_ids_from_request(body.exclude_ids),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    app_settings = settings_svc.get_app_settings(session)
    return _job_response(
        job,
        cron_timezone=app_settings.cron_timezone,
        cron_local_zone=app_settings.cron_local_zone,
        last_run=_last_run_for(session, job),
    )


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
    "/{job_id}/clone",
    response_model=JobResponse,
    dependencies=[Depends(require_csrf)],
)
def clone_job(job_id: int, _user: CurrentUserDep, session: SessionDep) -> JobResponse:
    job = job_svc.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    try:
        cloned = job_svc.clone_job(session, job)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    app_settings = settings_svc.get_app_settings(session)
    return _job_response(
        cloned,
        cron_timezone=app_settings.cron_timezone,
        cron_local_zone=app_settings.cron_local_zone,
        last_run=None,
    )


@router.post(
    "/{job_id}/exclude-ids",
    response_model=JobResponse,
    dependencies=[Depends(require_csrf)],
)
def append_job_exclude_ids(
    job_id: int,
    body: ExcludeIds,
    _user: CurrentUserDep,
    session: SessionDep,
) -> JobResponse:
    """Merge TMDB/IMDb/TVDB ids into a job's exclude list."""
    job = job_svc.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job = job_svc.append_exclude_ids(
        session,
        job,
        {"tmdb": body.tmdb, "imdb": body.imdb, "tvdb": body.tvdb},
    )
    app_settings = settings_svc.get_app_settings(session)
    return _job_response(
        job,
        cron_timezone=app_settings.cron_timezone,
        cron_local_zone=app_settings.cron_local_zone,
        last_run=_last_run_for(session, job),
    )


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
    dry_run, _coerced = resolve_dry_run(session, job, dry_run_override=dry_run_override)

    run = JobRun(job_id=job_id, job_name=job.name, trigger=RunTrigger.MANUAL, dry_run=dry_run)
    session.add(run)
    session.commit()
    session.refresh(run)

    try:
        run = get_scheduler_manager().enqueue_now(
            job_id,
            dry_run_override=dry_run_override,
            run=run,
        )
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
