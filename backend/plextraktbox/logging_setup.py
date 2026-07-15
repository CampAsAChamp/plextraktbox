"""structlog configuration with per-run DB persistence and live pub/sub."""

from __future__ import annotations

import logging
import os
import re
import sys
from typing import cast

import structlog
from structlog.dev import Column, ConsoleRenderer, KeyValueColumnFormatter

from plextraktbox.config import get_settings
from plextraktbox.logstream.handler import redact_log_processor, run_log_processor

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

# Longer verbs first so "POST" does not steal a prefix of a future inventively named verb.
_HTTP_METHOD_RE = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)(?=\s|$)")

# Postman / Insomnia-adjacent verb colors (bright ANSI) for terminal access logs.
_HTTP_METHOD_COLORS = {
    "GET": "\x1b[94m",
    "POST": "\x1b[92m",
    "PUT": "\x1b[93m",
    "PATCH": "\x1b[95m",
    "DELETE": "\x1b[91m",
    "HEAD": "\x1b[96m",
    "OPTIONS": "\x1b[90m",
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


class _HttpMethodEventFormatter:
    """Color the leading HTTP verb in access-log event text (e.g. GET /api/...)."""

    def __init__(
        self,
        *,
        value_style: str,
        method_styles: dict[str, str],
        reset_style: str,
        width: int = 30,
    ) -> None:
        self._value_style = value_style
        self._method_styles = method_styles
        self._reset_style = reset_style
        self._width = width

    def __call__(self, key: str, value: object) -> str:
        text = str(value)
        pad = max(0, self._width - len(text))
        padded = text + (" " * pad)
        match = _HTTP_METHOD_RE.match(padded)
        if match is None:
            return f"{self._value_style}{padded}{self._reset_style}"

        method = match.group(1)
        rest = padded[len(method) :]
        method_style = self._method_styles.get(method, self._value_style)
        return (
            f"{method_style}{method}{self._reset_style}"
            f"{self._value_style}{rest}{self._reset_style}"
        )


class _HttpMethodValueFormatter:
    """Color method=GET|PUT|... key/value pairs in console output."""

    def __init__(
        self,
        *,
        key_style: str,
        method_styles: dict[str, str],
        fallback_value_style: str,
        reset_style: str,
    ) -> None:
        self._key_style = key_style
        self._method_styles = method_styles
        self._fallback_value_style = fallback_value_style
        self._reset_style = reset_style

    def __call__(self, key: str, value: object) -> str:
        text = str(value)
        method_style = self._method_styles.get(text, self._fallback_value_style)
        return (
            f"{self._key_style}{key}{self._reset_style}="
            f"{method_style}{text}{self._reset_style}"
        )


def _http_method_styles(*, colors: bool) -> dict[str, str]:
    if not colors:
        return dict.fromkeys(_HTTP_METHOD_COLORS, "")
    return dict(_HTTP_METHOD_COLORS)


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
    method_styles = _http_method_styles(colors=colors)

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
                _HttpMethodEventFormatter(
                    value_style=styles.bright,
                    method_styles=method_styles,
                    reset_style=styles.reset,
                    width=30,
                ),
            ),
            Column("logger", logger_name_formatter),
            Column("logger_name", logger_name_formatter),
            Column(
                "method",
                _HttpMethodValueFormatter(
                    key_style=styles.kv_key,
                    method_styles=method_styles,
                    fallback_value_style=styles.kv_value,
                    reset_style=styles.reset,
                ),
            ),
        ],
    )


def _resolve_log_format(settings: object) -> str:
    log_format = getattr(settings, "log_format", "auto")
    env = getattr(settings, "env", "local")
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
        redact_log_processor,
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
