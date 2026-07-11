"""Job persistence helpers."""

from __future__ import annotations

from sqlmodel import Session, select

from plextraktbox.models.job import Job, SourcePair
from plextraktbox.scheduler import get_scheduler_manager
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
    cron: str,
    dry_run: bool,
    data_types: set[DataType],
) -> Job:
    job = Job(
        name=name,
        source_pair=source_pair,
        enabled=enabled,
        cron=cron,
        dry_run=dry_run,
        data_types_json=Job.dump_data_types(data_types),
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
) -> Job:
    job.name = name
    job.source_pair = source_pair
    job.enabled = enabled
    job.cron = cron
    job.dry_run = dry_run
    job.data_types_json = Job.dump_data_types(data_types)
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
