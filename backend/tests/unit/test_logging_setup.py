from __future__ import annotations

from plextraktbox.logging_setup import (
    _UppercaseLogLevelFormatter,
    _strip_logger_prefix,
)


def test_uppercase_log_level_formatter_uses_compact_brackets() -> None:
    formatter = _UppercaseLogLevelFormatter(level_styles={}, reset_style="")

    assert formatter("level", "info") == "[INFO]"
    assert formatter("level", "warning") == "[WARN]"
    assert formatter("level", "error") == "[ERROR]"
    assert formatter("level", "critical") == "[CRITICAL]"


def test_strip_logger_prefix_removes_package_name() -> None:
    event_dict = {"logger_name": "plextraktbox.http_access", "logger": "plextraktbox.main"}

    result = _strip_logger_prefix(None, "info", event_dict)

    assert result["logger_name"] == "http_access"
    assert result["logger"] == "main"


def test_strip_logger_prefix_leaves_other_loggers_unchanged() -> None:
    event_dict = {"logger_name": "uvicorn.error"}

    result = _strip_logger_prefix(None, "info", event_dict)

    assert result["logger_name"] == "uvicorn.error"
