"""structlog configuration.

The per-run log pipeline (DB persistence + SSE pub/sub) is layered on top of this
baseline in Phase 5. This module sets up console rendering for app-level logs.
"""

from __future__ import annotations

import logging
import os
import sys

import structlog

from plextraktbox.config import get_settings


def _resolve_log_format(settings: object) -> str:
    log_format = getattr(settings, "log_format", "auto")
    env = getattr(settings, "env", "dev")
    if log_format == "auto":
        return "json" if env == "prod" else "console"
    return log_format


def _use_colors(log_format: str) -> bool:
    if log_format != "console":
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR") or os.environ.get("CLICOLOR_FORCE"):
        return True
    return sys.stderr.isatty()


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_format = _resolve_log_format(settings)
    use_colors = _use_colors(log_format)

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors: list[object] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.ExtraAdder(),
    ]

    if log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=use_colors)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # httpx logs raw outbound requests at INFO; oauth poll handlers emit structured events.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
