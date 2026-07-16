"""APScheduler lifecycle: register cron jobs and enqueue manual runs."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlmodel import Session, select

from plextraktbox import db
from plextraktbox.cron import DEFAULT_CRON_TIMEZONE, resolve_cron_timezone
from plextraktbox.logging_setup import get_logger
from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.scheduler.runner import execute_run
from plextraktbox.scheduler.system_jobs import (
    CONNECTION_HEALTH_CRON,
    CONNECTION_HEALTH_JOB_ID,
    LOG_RETENTION_CRON,
    LOG_RETENTION_JOB_ID,
    run_connection_health_checks,
    run_log_retention,
)
from plextraktbox.services import settings as settings_svc

log = get_logger(__name__)

SCHEDULED_JOB_PREFIX = "sync_job_"
MANUAL_JOB_PREFIX = "manual_run_"
MANUAL_WAIT_TIMEOUT_S = 300
MANUAL_POLL_INTERVAL_S = 0.1


class SchedulerManager:
    def __init__(self) -> None:
        self._scheduler: AsyncIOScheduler | None = None

    @property
    def scheduler(self) -> AsyncIOScheduler:
        if self._scheduler is None:
            raise RuntimeError("Scheduler has not been started")
        return self._scheduler

    @property
    def running(self) -> bool:
        return self._scheduler is not None and self._scheduler.running

    def start(self) -> None:
        if self._scheduler is not None:
            return
        jobstores = {"default": SQLAlchemyJobStore(engine=db.engine)}
        self._scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")
        self._scheduler.start()
        self.load_all_jobs()
        self.register_system_jobs()
        log.info("scheduler.started")

    def register_system_jobs(self) -> None:
        if self._scheduler is None:
            return
        self._scheduler.add_job(
            run_connection_health_checks,
            trigger=CronTrigger.from_crontab(CONNECTION_HEALTH_CRON, timezone="UTC"),
            id=CONNECTION_HEALTH_JOB_ID,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        self._scheduler.add_job(
            run_log_retention,
            trigger=CronTrigger.from_crontab(LOG_RETENTION_CRON, timezone="UTC"),
            id=LOG_RETENTION_JOB_ID,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        log.info("scheduler.system_jobs.registered")

    def shutdown(self, *, wait: bool = True) -> None:
        if self._scheduler is None:
            return
        self._scheduler.shutdown(wait=wait)
        self._scheduler = None
        log.info("scheduler.stopped")

    def load_all_jobs(self) -> None:
        with Session(db.engine) as session:
            jobs = list(session.exec(select(Job)).all())
        for job in jobs:
            self.sync_job(job)

    def _cron_timezone(self) -> str:
        with Session(db.engine) as session:
            settings = settings_svc.get_app_settings(session)
            preference = settings.cron_timezone or DEFAULT_CRON_TIMEZONE
            return resolve_cron_timezone(preference, local_zone=settings.cron_local_zone)

    def sync_job(self, job: Job) -> None:
        if self._scheduler is None:
            return
        if job.id is None:
            return

        job_id = job.id
        aps_id = f"{SCHEDULED_JOB_PREFIX}{job_id}"
        existing = self._scheduler.get_job(aps_id)
        if existing is not None:
            self._scheduler.remove_job(aps_id)

        if not job.enabled:
            log.info("scheduler.job.removed", job_id=job_id, reason="disabled")
            return

        cron_timezone = self._cron_timezone()
        try:
            trigger = CronTrigger.from_crontab(job.cron, timezone=cron_timezone)
        except ValueError as exc:
            log.warning("scheduler.job.invalid_cron", job_id=job_id, cron=job.cron, error=str(exc))
            return

        self._scheduler.add_job(
            execute_run,
            trigger=trigger,
            id=aps_id,
            kwargs={"job_id": job_id, "trigger": RunTrigger.SCHEDULED},
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        log.info(
            "scheduler.job.registered",
            job_id=job_id,
            cron=job.cron,
            timezone=cron_timezone,
        )

    def remove_job(self, job_id: int) -> None:
        if self._scheduler is None:
            return
        aps_id = f"{SCHEDULED_JOB_PREFIX}{job_id}"
        existing = self._scheduler.get_job(aps_id)
        if existing is not None:
            self._scheduler.remove_job(aps_id)
            log.info("scheduler.job.removed", job_id=job_id)

    def get_next_run_time(self, job_id: int) -> datetime | None:
        """Return the next scheduled fire time for a job, or None if unscheduled."""
        if self._scheduler is None:
            return None
        aps_job = self._scheduler.get_job(f"{SCHEDULED_JOB_PREFIX}{job_id}")
        if aps_job is None or aps_job.next_run_time is None:
            return None
        nxt = aps_job.next_run_time
        if nxt.tzinfo is None:
            return nxt.replace(tzinfo=UTC)
        return nxt.astimezone(UTC)

    def trigger_now(
        self,
        job_id: int,
        *,
        dry_run_override: bool | None = None,
        run: JobRun,
    ) -> JobRun:
        """Enqueue a manual run and block until it finishes."""
        if self._scheduler is None:
            raise RuntimeError("Scheduler has not been started")
        if run.id is None:
            raise ValueError("JobRun must be persisted before triggering")

        run_id = run.id
        aps_id = f"{MANUAL_JOB_PREFIX}{run_id}"
        self._scheduler.add_job(
            execute_run,
            trigger=DateTrigger(run_date=datetime.now(UTC)),
            id=aps_id,
            kwargs={
                "job_id": job_id,
                "trigger": RunTrigger.MANUAL,
                "dry_run_override": dry_run_override,
                "run_id": run_id,
            },
            max_instances=1,
            replace_existing=True,
        )

        deadline = time.monotonic() + MANUAL_WAIT_TIMEOUT_S
        while time.monotonic() < deadline:
            with Session(db.engine) as session:
                current = session.get(JobRun, run_id)
                if current is None:
                    raise ValueError(f"JobRun {run_id} not found")
                if current.status != JobRunStatus.RUNNING:
                    return current
            time.sleep(MANUAL_POLL_INTERVAL_S)

        raise TimeoutError(f"Job run {run_id} did not complete within {MANUAL_WAIT_TIMEOUT_S}s")


_manager: SchedulerManager | None = None


def get_scheduler_manager() -> SchedulerManager:
    global _manager
    if _manager is None:
        _manager = SchedulerManager()
    return _manager
