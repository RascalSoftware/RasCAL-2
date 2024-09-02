"""Tests for configuration utilities."""

import tempfile
from logging import CRITICAL, INFO, WARNING

import pytest

from rascal2.config import setup_logging, setup_settings
from rascal2.core.settings import LogLevels, Settings


def test_setup_settings():
    """Test that settings are grabbed from JSON or made from scratch correctly."""
    sets = setup_settings(".")
    assert sets == Settings()
    with tempfile.TemporaryDirectory() as tmp:
        settings1 = Settings(editor_fontsize=21, log_level=LogLevels.Critical)
        settings1.save(tmp)
        sets_from_json = setup_settings(tmp)
        assert sets_from_json == settings1


@pytest.mark.parametrize("level", [INFO, WARNING, CRITICAL])
def test_setup_logging(level):
    """Test that the logger is set up correctly."""
    with tempfile.TemporaryFile() as tmp:
        log = setup_logging(tmp, level)

    assert log.level == level
    assert log.hasHandlers()
