"""Job persistence helpers."""

from __future__ import annotations

from sqlmodel import Session, select

from plextraktbox.models.job import Job, NotifyMode, SourcePair
from plextraktbox.scheduler import get_scheduler_manager
from plextraktbox.services import settings as settings_svc
from plextraktbox.sync.excludes import dump_exclude_ids
from plextraktbox.sync.plans import DataType


def list_jobs(session: Session) -> list[Job]:
    return list(session.exec(select(Job).order_by(Job.id)).all())  # type: ignore[arg-type]


def get_job(session: Session, job_id: int) -> Job | None:
    return session.get(Job, job_id)


def create_job(
    session: Session,
    *,
    name: str,
    source_pair: SourcePair,
    enabled: bool,
    cron: str | None,
    dry_run: bool | None,
    data_types: set[DataType],
    notify_mode: NotifyMode = NotifyMode.INHERIT,
    require_dry_run_first: bool = True,
    exclude_ids: dict[str, list[str]] | None = None,
) -> Job:
    app_settings = settings_svc.ensure_defaults(session)
    resolved_cron = cron if cron is not None else app_settings.default_cron
    resolved_dry_run = dry_run if dry_run is not None else app_settings.global_dry_run
    job = Job(
        name=name,
        source_pair=source_pair,
        enabled=enabled,
        cron=resolved_cron,
        dry_run=resolved_dry_run,
        require_dry_run_first=require_dry_run_first,
        data_types_json=Job.dump_data_types(data_types),
        notify_override_json=Job.dump_notify_mode(notify_mode),
        exclude_ids_json=Job.dump_exclude_ids(exclude_ids or {}),
    )
    errors = job.validate_data_types()
    if errors:
        raise ValueError("; ".join(errors))
    session.add(job)
    session.commit()
    session.refresh(job)
    get_scheduler_manager().sync_job(job)
    return job


def update_job(
    session: Session,
    job: Job,
    *,
    name: str,
    source_pair: SourcePair,
    enabled: bool,
    cron: str,
    dry_run: bool,
    data_types: set[DataType],
    notify_mode: NotifyMode = NotifyMode.INHERIT,
    require_dry_run_first: bool = True,
    exclude_ids: dict[str, list[str]] | None = None,
) -> Job:
    job.name = name
    job.source_pair = source_pair
    job.enabled = enabled
    job.cron = cron
    job.dry_run = dry_run
    job.require_dry_run_first = require_dry_run_first
    job.data_types_json = Job.dump_data_types(data_types)
    job.notify_override_json = Job.dump_notify_mode(notify_mode)
    job.exclude_ids_json = Job.dump_exclude_ids(exclude_ids or {})
    errors = job.validate_data_types()
    if errors:
        raise ValueError("; ".join(errors))
    session.add(job)
    session.commit()
    session.refresh(job)
    get_scheduler_manager().sync_job(job)
    return job


def delete_job(session: Session, job: Job) -> None:
    job_id = job.id
    if job_id is not None:
        get_scheduler_manager().remove_job(job_id)
    session.delete(job)
    session.commit()


def _unique_clone_name(session: Session, base_name: str) -> str:
    """Return ``"{base} (copy)"`` or ``"{base} (copy N)"`` if names collide."""
    candidate = f"{base_name} (copy)"
    existing = {job.name for job in list_jobs(session)}
    if candidate not in existing:
        return candidate
    n = 2
    while f"{base_name} (copy {n})" in existing:
        n += 1
    return f"{base_name} (copy {n})"


def clone_job(session: Session, job: Job) -> Job:
    """Duplicate a job's config. Clones start disabled (safe default)."""
    return create_job(
        session,
        name=_unique_clone_name(session, job.name),
        source_pair=job.source_pair,
        enabled=False,
        cron=job.cron,
        dry_run=job.dry_run,
        data_types=job.data_types(),
        notify_mode=job.notify_mode(),
        require_dry_run_first=job.require_dry_run_first,
        exclude_ids=dump_exclude_ids(job.exclude_ids()),
    )
