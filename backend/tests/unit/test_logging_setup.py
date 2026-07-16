from __future__ import annotations

import logging
import sys

from plextraktbox.logging_setup import (
    _HTTP_METHOD_COLORS,
    _HttpMethodEventFormatter,
    _HttpMethodValueFormatter,
    _UppercaseLogLevelFormatter,
    _http_method_styles,
    _strip_logger_prefix,
    _uvicorn_color_message,
    configure_logging,
)


def test_uppercase_log_level_formatter_uses_compact_brackets() -> None:
    formatter = _UppercaseLogLevelFormatter(level_styles={}, reset_style="")

    assert formatter("level", "info") == "[INFO]"
    assert formatter("level", "warning") == "[WARN]"
    assert formatter("level", "error") == "[ERROR]"
    assert formatter("level", "critical") == "[CRITICAL]"


def test_http_method_event_formatter_colors_leading_verb() -> None:
    formatter = _HttpMethodEventFormatter(
        value_style="",
        method_styles=_HTTP_METHOD_COLORS,
        reset_style="\x1b[0m",
        width=0,
    )

    rendered = formatter("event", "PUT /api/settings/theme 200")

    assert rendered == (
        f"{_HTTP_METHOD_COLORS['PUT']}PUT\x1b[0m /api/settings/theme 200\x1b[0m"
    )


def test_http_method_event_formatter_leaves_plain_events_unchanged() -> None:
    formatter = _HttpMethodEventFormatter(
        value_style="",
        method_styles=_HTTP_METHOD_COLORS,
        reset_style="",
        width=0,
    )

    assert formatter("event", "scheduler.started") == "scheduler.started"


def test_http_method_value_formatter_colors_known_verbs() -> None:
    formatter = _HttpMethodValueFormatter(
        key_style="",
        method_styles=_HTTP_METHOD_COLORS,
        fallback_value_style="",
        reset_style="\x1b[0m",
    )

    assert formatter("method", "GET") == f"method\x1b[0m={_HTTP_METHOD_COLORS['GET']}GET\x1b[0m"
    assert (
        formatter("method", "DELETE")
        == f"method\x1b[0m={_HTTP_METHOD_COLORS['DELETE']}DELETE\x1b[0m"
    )


def test_http_method_styles_disabled_without_color() -> None:
    styles = _http_method_styles(colors=False)

    assert styles["GET"] == ""
    assert styles["PUT"] == ""


def test_strip_logger_prefix_removes_package_name() -> None:
    event_dict = {"logger_name": "plextraktbox.http_access", "logger": "plextraktbox.main"}

    result = _strip_logger_prefix(None, "info", event_dict)

    assert result["logger_name"] == "http_access"
    assert result["logger"] == "main"


def test_strip_logger_prefix_leaves_other_loggers_unchanged() -> None:
    event_dict = {"logger_name": "uvicorn.error"}

    result = _strip_logger_prefix(None, "info", event_dict)

    assert result["logger_name"] == "uvicorn.error"


def test_uvicorn_color_message_dropped_without_colors() -> None:
    record = logging.LogRecord(
        name="uvicorn.error",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Finished server process [%d]",
        args=(184,),
        exc_info=None,
    )
    event_dict = {
        "event": "Finished server process [184]",
        "color_message": "Finished server process [\x1b[36m%d\x1b[0m]",
        "_record": record,
    }

    result = _uvicorn_color_message(colors=False)(None, "info", event_dict)

    assert "color_message" not in result
    assert result["event"] == "Finished server process [184]"


def test_uvicorn_color_message_applied_with_colors() -> None:
    record = logging.LogRecord(
        name="uvicorn.error",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Finished server process [%d]",
        args=(184,),
        exc_info=None,
    )
    event_dict = {
        "event": "Finished server process [184]",
        "color_message": "Finished server process [\x1b[36m%d\x1b[0m]",
        "_record": record,
    }

    result = _uvicorn_color_message(colors=True)(None, "info", event_dict)

    assert "color_message" not in result
    assert result["event"] == "Finished server process [\x1b[36m184\x1b[0m]"


def test_configure_logging_writes_to_stdout() -> None:
    configure_logging()

    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0], logging.StreamHandler)
    assert root.handlers[0].stream is sys.stdout

    for name in ("uvicorn", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        assert uv_logger.handlers == []
        assert uv_logger.propagate is True

    access = logging.getLogger("uvicorn.access")
    assert access.handlers == []
    assert access.propagate is False
