"""mDNS discovery for Shelly devices."""

import contextlib
import logging
import time

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

from .consts import SHELLY_HTTP_MDNS_SERVICE_TYPE, SHELLY_MDNS_SERVICE_TYPE

_LOGGER = logging.getLogger(__name__)


class ShellyServiceListener(ServiceListener):
    """Listener for Shelly mDNS services."""

    def __init__(self, zc: Zeroconf):
        """Initialise listener."""
        self.zeroconf = zc
        self.devices = []

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service addition."""
        if self._is_shelly_service(type_, name):
            self._get_addresses(zc, type_, name)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service update."""
        if self._is_shelly_service(type_, name):
            self._get_addresses(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service removal."""

    def _is_shelly_service(self, type_: str, name: str) -> bool:
        """Check if the service belongs to a Shelly device."""
        if type_ == SHELLY_MDNS_SERVICE_TYPE:
            return True
        if type_ == SHELLY_HTTP_MDNS_SERVICE_TYPE:
            return "shelly" in name.lower()
        return False

    def _get_addresses(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Get IP addresses for a service."""
        info = zc.get_service_info(type_, name, timeout=5000)
        if info:
            addresses = info.parsed_addresses()
            for address in addresses:
                if address and address not in self.devices:
                    self.devices.append(address)
                    _LOGGER.info("Discovered Shelly device at %s", address)


def _collect_from_browser(zeroconf, browser, devices_set, devices_ordered):
    try:
        services = getattr(browser, "services", None)
        if not services:
            return
        service_type = getattr(browser, "type", SHELLY_MDNS_SERVICE_TYPE)
        for service_name in list(services.keys()):
            if (
                service_type == SHELLY_HTTP_MDNS_SERVICE_TYPE
                and "shelly" not in service_name.lower()
            ):
                continue
            with contextlib.suppress(OSError, RuntimeError):
                info = zeroconf.get_service_info(
                    service_type, service_name, timeout=3000
                )
                if info:
                    for addr in info.parsed_addresses():
                        if addr and addr not in devices_set:
                            devices_set.add(addr)
                            devices_ordered.append(addr)
                            _LOGGER.info("Discovered Shelly device at %s", addr)
    except OSError, RuntimeError:
        pass


def discover_shelly_devices(timeout: float = 60.0) -> list[str]:
    """Discover Shelly devices on the network via mDNS."""
    devices_set: set[str] = set()
    devices_ordered: list[str] = []

    zeroconf = Zeroconf()
    listener = ShellyServiceListener(zeroconf)
    browsers = []
    try:
        browsers.append(ServiceBrowser(zeroconf, SHELLY_MDNS_SERVICE_TYPE, listener))
        browsers.append(
            ServiceBrowser(zeroconf, SHELLY_HTTP_MDNS_SERVICE_TYPE, listener)
        )
        for _ in range(int(timeout)):
            time.sleep(1)
            for addr in listener.devices:
                if addr and addr not in devices_set:
                    devices_set.add(addr)
                    devices_ordered.append(addr)
                    _LOGGER.info("Discovered Shelly device at %s", addr)
            for browser in browsers:
                _collect_from_browser(zeroconf, browser, devices_set, devices_ordered)
    finally:
        with contextlib.suppress(OSError, RuntimeError):
            zeroconf.close()

    return devices_ordered
