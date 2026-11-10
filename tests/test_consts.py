"""Tests for constants."""

from shelly_backup import consts


def test_application_name():
    """Test application name constant."""
    assert consts.APPLICATION_NAME == "Shelly Backup"


def test_mdns_service_types():
    """Test mDNS service type constants."""
    assert consts.SHELLY_MDNS_SERVICE_TYPE == "_shelly._tcp.local."
    assert consts.SHELLY_HTTP_MDNS_SERVICE_TYPE == "_http._tcp.local."
