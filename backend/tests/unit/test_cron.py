"""Cron expression validation tests."""

from __future__ import annotations

import pytest

from plextraktbox.cron import validate_cron_expression


def test_validate_cron_expression_accepts_valid_expressions() -> None:
    assert validate_cron_expression("0 3 * * *") == "0 3 * * *"
    assert validate_cron_expression("  * * * * *  ") == "* * * * *"


@pytest.mark.parametrize(
    "expression",
    ["", "   ", "invalid", "0 3 * *", "99 99 99 99 99"],
)
def test_validate_cron_expression_rejects_invalid_expressions(expression: str) -> None:
    with pytest.raises(ValueError, match="Invalid cron expression|Cron expression is required"):
        validate_cron_expression(expression)
