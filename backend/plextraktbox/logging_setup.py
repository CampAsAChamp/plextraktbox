"""structlog configuration with per-run DB persistence and live pub/sub."""

from __future__ import annotations

import logging
import os
import sys
from typing import cast

import structlog
from structlog.dev import Column, ConsoleRenderer, KeyValueColumnFormatter

from plextraktbox.config import get_settings
from plextraktbox.logstream.handler import run_log_processor

_LEVEL_LABELS = {
    "critical": "CRITICAL",
    "exception": "ERROR",
    "error": "ERROR",
    "warning": "WARN",
    "warn": "WARN",
    "info": "INFO",
    "debug": "DEBUG",
    "notset": "NOTSET",
}


class _UppercaseLogLevelFormatter:
    """Format log levels as compact uppercase labels ([INFO], [WARN], ...)."""

    def __init__(self, level_styles: dict[str, str], reset_style: str) -> None:
        self._level_styles = level_styles
        self._reset_style = reset_style

    def __call__(self, key: str, value: object) -> str:
        raw = cast(str, value).lower()
        label = _LEVEL_LABELS.get(raw, raw.upper())
        style = self._level_styles.get(raw, "")
        return f"[{style}{label}{self._reset_style}]"


def _strip_logger_prefix(
    _logger: object, _method: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    for key in ("logger", "logger_name"):
        name = event_dict.get(key)
        if isinstance(name, str) and name.startswith("plextraktbox."):
            event_dict[key] = name.removeprefix("plextraktbox.")
    return event_dict


def _repr_value(val: object) -> str:
    if isinstance(val, str):
        if set(val) & {" ", "\t", "=", "\r", "\n", '"', "'"}:
            return repr(val)
        return val
    return repr(val)


def _console_renderer(*, colors: bool) -> ConsoleRenderer:
    styles = ConsoleRenderer.get_default_column_styles(colors)
    level_styles = ConsoleRenderer.get_default_level_styles(colors)
    for key in level_styles:
        level_styles[key] += styles.bright

    logger_name_formatter = KeyValueColumnFormatter(
        key_style=None,
        value_style=styles.bright + styles.logger_name,
        reset_style=styles.reset,
        value_repr=str,
        prefix="[",
        postfix="]",
    )

    default_formatter = KeyValueColumnFormatter(
        styles.kv_key,
        styles.kv_value,
        styles.reset,
        value_repr=_repr_value,
        width=0,
    )

    return ConsoleRenderer(
        columns=[
            Column("", default_formatter),
            Column(
                "timestamp",
                KeyValueColumnFormatter(
                    key_style=None,
                    value_style=styles.timestamp,
                    reset_style=styles.reset,
                    value_repr=str,
                ),
            ),
            Column(
                "level",
                _UppercaseLogLevelFormatter(level_styles, styles.reset),
            ),
            Column(
                "event",
                KeyValueColumnFormatter(
                    key_style=None,
                    value_style=styles.bright,
                    reset_style=styles.reset,
                    value_repr=str,
                    width=30,
                ),
            ),
            Column("logger", logger_name_formatter),
            Column("logger_name", logger_name_formatter),
        ],
    )


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
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _strip_logger_prefix,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.ExtraAdder(),
        run_log_processor,
    ]

    if log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = _console_renderer(colors=use_colors)

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
    # requests_cache stale-if-error recovery is handled by _QuietCachedSession.
    logging.getLogger("requests_cache").setLevel(logging.ERROR)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
