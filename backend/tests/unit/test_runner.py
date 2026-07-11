"""Dev run delay helper tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from plextraktbox.scheduler.runner import _apply_dev_run_delay


def test_dev_run_delay_skipped_in_prod() -> None:
    logger = MagicMock()
    with patch("plextraktbox.scheduler.runner.get_settings") as get_settings:
        get_settings.return_value.env = "prod"
        get_settings.return_value.sync_run_delay_seconds = 10
        with patch("plextraktbox.scheduler.runner.time.sleep") as sleep:
            _apply_dev_run_delay(logger)

    sleep.assert_not_called()
    logger.info.assert_not_called()


def test_dev_run_delay_skipped_when_zero() -> None:
    logger = MagicMock()
    with patch("plextraktbox.scheduler.runner.get_settings") as get_settings:
        get_settings.return_value.env = "dev"
        get_settings.return_value.sync_run_delay_seconds = 0
        with patch("plextraktbox.scheduler.runner.time.sleep") as sleep:
            _apply_dev_run_delay(logger)

    sleep.assert_not_called()
    logger.info.assert_not_called()


def test_dev_run_delay_logs_and_sleeps_each_second() -> None:
    logger = MagicMock()
    with patch("plextraktbox.scheduler.runner.get_settings") as get_settings:
        get_settings.return_value.env = "dev"
        get_settings.return_value.sync_run_delay_seconds = 3
        with patch("plextraktbox.scheduler.runner.time.sleep") as sleep:
            _apply_dev_run_delay(logger)

    assert sleep.call_count == 3
    logger.info.assert_any_call("sync.run.dev_delay.start", seconds=3)
    logger.info.assert_any_call("sync.run.dev_delay.tick", elapsed=1, total=3)
    logger.info.assert_any_call("sync.run.dev_delay.tick", elapsed=3, total=3)
