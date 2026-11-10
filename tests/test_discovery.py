"""Tests for mDNS discovery."""

from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import pytest

from shelly_backup import consts
from shelly_backup.discovery import (
    ShellyServiceListener,
    _collect_from_browser,
    discover_shelly_devices,
)


def _service_info(*addresses):
    """Create a mocked Zeroconf service info object."""
    info = Mock()
    info.parsed_addresses.return_value = list(addresses)
    return info


class TestShellyServiceListener:
    """Tests for ShellyServiceListener."""

    def test_init(self):
        """Test listener initialisation."""
        zeroconf = Mock()
        listener = ShellyServiceListener(zeroconf)
        assert listener.zeroconf is zeroconf
        assert listener.devices == []

    @pytest.mark.parametrize(
        ("service_type", "name", "expected"),
        [
            (
                consts.SHELLY_MDNS_SERVICE_TYPE,
                "shellyplus1-abc._shelly._tcp.local.",
                True,
            ),
            (
                consts.SHELLY_HTTP_MDNS_SERVICE_TYPE,
                "shelly1-abc._http._tcp.local.",
                True,
            ),
            (
                consts.SHELLY_HTTP_MDNS_SERVICE_TYPE,
                "SHELLY1-ABC._http._tcp.local.",
                True,
            ),
            (
                consts.SHELLY_HTTP_MDNS_SERVICE_TYPE,
                "printer._http._tcp.local.",
                False,
            ),
            ("_other._tcp.local.", "shelly1-abc._other._tcp.local.", False),
        ],
    )
    def test_is_shelly_service(self, service_type, name, expected):
        """Test identifying Shelly services across service types."""
        listener = ShellyServiceListener(Mock())
        assert listener._is_shelly_service(service_type, name) is expected  # noqa: SLF001

    @pytest.mark.parametrize("method_name", ["add_service", "update_service"])
    def test_add_and_update_service_for_shelly(self, method_name):
        """Test that Shelly services trigger an address lookup."""
        zeroconf = Mock()
        listener = ShellyServiceListener(zeroconf)
        with patch.object(listener, "_get_addresses") as mock_get_addresses:
            getattr(listener, method_name)(
                zeroconf, consts.SHELLY_MDNS_SERVICE_TYPE, "name"
            )
            mock_get_addresses.assert_called_once_with(
                zeroconf, consts.SHELLY_MDNS_SERVICE_TYPE, "name"
            )

    @pytest.mark.parametrize("method_name", ["add_service", "update_service"])
    def test_add_and_update_service_for_non_shelly(self, method_name):
        """Test that unrelated HTTP services are ignored."""
        zeroconf = Mock()
        listener = ShellyServiceListener(zeroconf)
        with patch.object(listener, "_get_addresses") as mock_get_addresses:
            getattr(listener, method_name)(
                zeroconf,
                consts.SHELLY_HTTP_MDNS_SERVICE_TYPE,
                "printer._http._tcp.local.",
            )
            mock_get_addresses.assert_not_called()

    def test_remove_service(self):
        """Test that removing a service leaves discovered devices untouched."""
        listener = ShellyServiceListener(Mock())
        listener.devices = ["192.168.1.10"]
        listener.remove_service(Mock(), consts.SHELLY_MDNS_SERVICE_TYPE, "name")
        assert listener.devices == ["192.168.1.10"]

    def test_get_addresses(self):
        """Test resolving and storing service addresses."""
        zeroconf = Mock()
        zeroconf.get_service_info.return_value = _service_info(
            "192.168.1.10", "192.168.1.11"
        )
        listener = ShellyServiceListener(zeroconf)
        listener._get_addresses(  # noqa: SLF001
            zeroconf, consts.SHELLY_MDNS_SERVICE_TYPE, "name"
        )
        assert listener.devices == ["192.168.1.10", "192.168.1.11"]
        zeroconf.get_service_info.assert_called_once_with(
            consts.SHELLY_MDNS_SERVICE_TYPE, "name", timeout=5000
        )

    def test_get_addresses_deduplicates_and_skips_empty(self):
        """Test that duplicate and empty addresses are ignored."""
        zeroconf = Mock()
        zeroconf.get_service_info.return_value = _service_info(
            "", None, "192.168.1.10", "192.168.1.10", "192.168.1.11"
        )
        listener = ShellyServiceListener(zeroconf)
        listener.devices = ["192.168.1.10"]
        listener._get_addresses(  # noqa: SLF001
            zeroconf, consts.SHELLY_MDNS_SERVICE_TYPE, "name"
        )
        assert listener.devices == ["192.168.1.10", "192.168.1.11"]

    def test_get_addresses_without_info(self):
        """Test that unresolved services add no devices."""
        zeroconf = Mock()
        zeroconf.get_service_info.return_value = None
        listener = ShellyServiceListener(zeroconf)
        listener._get_addresses(  # noqa: SLF001
            zeroconf, consts.SHELLY_MDNS_SERVICE_TYPE, "name"
        )
        assert listener.devices == []


class TestCollectFromBrowser:
    """Tests for _collect_from_browser."""

    def test_without_services(self):
        """Test that a browser without services is ignored."""
        zeroconf = Mock()
        devices_set = set()
        devices_ordered = []
        _collect_from_browser(
            zeroconf, Mock(services=None), devices_set, devices_ordered
        )
        assert devices_set == set()
        assert devices_ordered == []
        zeroconf.get_service_info.assert_not_called()

    def test_with_empty_services(self):
        """Test that a browser with an empty service list is ignored."""
        zeroconf = Mock()
        devices_set = set()
        devices_ordered = []
        _collect_from_browser(zeroconf, Mock(services={}), devices_set, devices_ordered)
        assert devices_ordered == []
        zeroconf.get_service_info.assert_not_called()

    def test_collects_shelly_services(self):
        """Test collecting addresses from a Shelly service browser."""
        zeroconf = Mock()
        zeroconf.get_service_info.side_effect = [
            _service_info("192.168.1.10"),
            _service_info("192.168.1.11", "192.168.1.10"),
        ]
        browser = SimpleNamespace(
            type=consts.SHELLY_MDNS_SERVICE_TYPE,
            services={"one": object(), "two": object()},
        )
        devices_set = set()
        devices_ordered = []

        _collect_from_browser(zeroconf, browser, devices_set, devices_ordered)

        assert devices_set == {"192.168.1.10", "192.168.1.11"}
        assert devices_ordered == ["192.168.1.10", "192.168.1.11"]
        assert zeroconf.get_service_info.call_args_list == [
            call(consts.SHELLY_MDNS_SERVICE_TYPE, "one", timeout=3000),
            call(consts.SHELLY_MDNS_SERVICE_TYPE, "two", timeout=3000),
        ]

    def test_skips_existing_addresses(self):
        """Test that already collected addresses are not added again."""
        zeroconf = Mock()
        zeroconf.get_service_info.return_value = _service_info(
            "192.168.1.10", "192.168.1.11"
        )
        browser = SimpleNamespace(
            type=consts.SHELLY_MDNS_SERVICE_TYPE,
            services={"one": object()},
        )
        devices_set = {"192.168.1.10"}
        devices_ordered = ["192.168.1.10"]

        _collect_from_browser(zeroconf, browser, devices_set, devices_ordered)

        assert devices_ordered == ["192.168.1.10", "192.168.1.11"]

    def test_skips_non_shelly_http_services(self):
        """Test that only HTTP services with a Shelly name are resolved."""
        zeroconf = Mock()
        zeroconf.get_service_info.return_value = _service_info("192.168.1.10")
        browser = SimpleNamespace(
            type=consts.SHELLY_HTTP_MDNS_SERVICE_TYPE,
            services={
                "shelly1-abc._http._tcp.local.": object(),
                "printer._http._tcp.local.": object(),
            },
        )
        devices_set = set()
        devices_ordered = []

        _collect_from_browser(zeroconf, browser, devices_set, devices_ordered)

        assert devices_ordered == ["192.168.1.10"]
        zeroconf.get_service_info.assert_called_once_with(
            consts.SHELLY_HTTP_MDNS_SERVICE_TYPE,
            "shelly1-abc._http._tcp.local.",
            timeout=3000,
        )

    def test_defaults_to_shelly_service_type(self):
        """Test that a browser without a type defaults to the Shelly service type."""
        zeroconf = Mock()
        zeroconf.get_service_info.return_value = _service_info("192.168.1.10")
        browser = SimpleNamespace(services={"anything": object()})
        devices_ordered = []

        _collect_from_browser(zeroconf, browser, set(), devices_ordered)

        assert devices_ordered == ["192.168.1.10"]
        zeroconf.get_service_info.assert_called_once_with(
            consts.SHELLY_MDNS_SERVICE_TYPE, "anything", timeout=3000
        )

    def test_ignores_service_errors(self):
        """Test that errors resolving a single service are suppressed."""
        zeroconf = Mock()
        zeroconf.get_service_info.side_effect = OSError("boom")
        browser = SimpleNamespace(
            type=consts.SHELLY_MDNS_SERVICE_TYPE,
            services={"one": object()},
        )
        devices_ordered = []

        _collect_from_browser(zeroconf, browser, set(), devices_ordered)

        assert devices_ordered == []

    def test_ignores_browser_errors(self):
        """Test that errors reading the browser's services are suppressed."""

        class BrokenBrowser:
            """Browser that fails when reading its services."""

            @property
            def services(self):
                """Raise an error when services are accessed."""
                raise RuntimeError("boom")

        devices_ordered = []

        _collect_from_browser(Mock(), BrokenBrowser(), set(), devices_ordered)

        assert devices_ordered == []


class TestDiscoverShellyDevices:
    """Tests for discover_shelly_devices."""

    @patch("shelly_backup.discovery.time.sleep")
    @patch("shelly_backup.discovery.ServiceBrowser")
    @patch("shelly_backup.discovery.Zeroconf")
    def test_discovery(self, mock_zeroconf_class, mock_browser_class, mock_sleep):
        """Test discovering devices from both Shelly and HTTP service types."""
        zeroconf = mock_zeroconf_class.return_value
        listeners = []

        def create_browser(_zeroconf, service_type, listener):
            listeners.append(listener)
            browser = Mock()
            browser.type = service_type
            browser.services = {}
            return browser

        mock_browser_class.side_effect = create_browser

        def sleep(_seconds):
            if len(mock_sleep.call_args_list) == 1:
                listeners[0].devices.extend(
                    ["192.168.1.10", "192.168.1.10", "192.168.1.11", ""]
                )

        mock_sleep.side_effect = sleep

        result = discover_shelly_devices(timeout=2)

        assert result == ["192.168.1.10", "192.168.1.11"]
        assert mock_sleep.call_count == 2
        assert mock_browser_class.call_args_list == [
            call(zeroconf, consts.SHELLY_MDNS_SERVICE_TYPE, listeners[0]),
            call(zeroconf, consts.SHELLY_HTTP_MDNS_SERVICE_TYPE, listeners[0]),
        ]
        zeroconf.close.assert_called_once()

    @patch("shelly_backup.discovery.time.sleep")
    @patch("shelly_backup.discovery.ServiceBrowser")
    @patch("shelly_backup.discovery.Zeroconf")
    def test_discovery_collects_from_browsers(
        self, mock_zeroconf_class, mock_browser_class, mock_sleep
    ):
        """Test that both browsers contribute discovered devices."""
        zeroconf = mock_zeroconf_class.return_value
        services = {
            consts.SHELLY_MDNS_SERVICE_TYPE: {"gen2._shelly._tcp.local.": object()},
            consts.SHELLY_HTTP_MDNS_SERVICE_TYPE: {
                "shelly1-abc._http._tcp.local.": object(),
                "printer._http._tcp.local.": object(),
            },
        }

        def create_browser(_zeroconf, service_type, _listener):
            browser = Mock()
            browser.type = service_type
            browser.services = services[service_type]
            return browser

        mock_browser_class.side_effect = create_browser

        def get_service_info(service_type, _name, timeout):  # noqa: ARG001
            if service_type == consts.SHELLY_MDNS_SERVICE_TYPE:
                return _service_info("192.168.1.10")
            return _service_info("192.168.1.11")

        zeroconf.get_service_info.side_effect = get_service_info

        result = discover_shelly_devices(timeout=1)

        assert result == ["192.168.1.10", "192.168.1.11"]
        assert zeroconf.get_service_info.call_args_list == [
            call(
                consts.SHELLY_MDNS_SERVICE_TYPE,
                "gen2._shelly._tcp.local.",
                timeout=3000,
            ),
            call(
                consts.SHELLY_HTTP_MDNS_SERVICE_TYPE,
                "shelly1-abc._http._tcp.local.",
                timeout=3000,
            ),
        ]

    @patch("shelly_backup.discovery.time.sleep")
    @patch("shelly_backup.discovery.ServiceBrowser")
    @patch("shelly_backup.discovery.Zeroconf")
    def test_discovery_without_timeout(
        self, mock_zeroconf_class, mock_browser_class, mock_sleep
    ):
        """Test that a zero timeout performs no discovery cycles."""
        zeroconf = mock_zeroconf_class.return_value

        result = discover_shelly_devices(timeout=0)

        assert result == []
        mock_sleep.assert_not_called()
        assert mock_browser_class.call_count == 2
        zeroconf.close.assert_called_once()

    @patch("shelly_backup.discovery.time.sleep")
    @patch("shelly_backup.discovery.ServiceBrowser")
    @patch("shelly_backup.discovery.Zeroconf")
    def test_discovery_closes_zeroconf_on_error(
        self, mock_zeroconf_class, mock_browser_class, mock_sleep
    ):
        """Test that Zeroconf is closed when discovery fails."""
        zeroconf = mock_zeroconf_class.return_value
        mock_sleep.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            discover_shelly_devices(timeout=1)

        zeroconf.close.assert_called_once()

    @patch("shelly_backup.discovery.time.sleep")
    @patch("shelly_backup.discovery.ServiceBrowser")
    @patch("shelly_backup.discovery.Zeroconf")
    def test_discovery_suppresses_close_errors(
        self, mock_zeroconf_class, mock_browser_class, mock_sleep
    ):
        """Test that errors while closing Zeroconf are suppressed."""
        zeroconf = mock_zeroconf_class.return_value
        zeroconf.close.side_effect = OSError("boom")

        result = discover_shelly_devices(timeout=0)

        assert result == []
