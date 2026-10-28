"""Tests for constants."""

from shelly_backup import consts


def test_application_name():
    """Test application name constant."""
    assert consts.APPLICATION_NAME == "Shelly Backup"
