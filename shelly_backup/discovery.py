"""mDNS discovery for Shelly devices."""

import logging
import time

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

from .consts import SHELLY_MDNS_SERVICE_TYPE

_LOGGER = logging.getLogger(__name__)


class ShellyServiceListener(ServiceListener):
    """Listener for Shelly mDNS services."""

    def __init__(self, zc: Zeroconf):
        """Initialise listener."""
        self.zeroconf = zc
        self.devices = []

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service addition."""
        self._get_addresses(zc, type_, name)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service update."""
        self._get_addresses(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service removal."""

    def _get_addresses(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Get IP addresses for a service."""
        info = zc.get_service_info(type_, name, timeout=3000)
        if info:
            addresses = info.parsed_addresses()
            for address in addresses:
                if address and address not in self.devices:
                    self.devices.append(address)
                    _LOGGER.info("Discovered Shelly device at %s", address)


def discover_shelly_devices(timeout: float = 30.0) -> list[str]:
    """Discover Shelly devices on the network via mDNS."""
    zeroconf = Zeroconf()
    listener = ShellyServiceListener(zeroconf)
    browser = ServiceBrowser(zeroconf, SHELLY_MDNS_SERVICE_TYPE, listener)
    try:
        time.sleep(timeout)
        # Also try to request info for any services found
        try:
            services = getattr(browser, "services", {}) or {}
            for service in list(services.keys()):
                try:
                    info = zeroconf.get_service_info(
                        SHELLY_MDNS_SERVICE_TYPE, service, timeout=2000
                    )
                    if info:
                        for address in info.parsed_addresses():
                            if address and address not in listener.devices:
                                listener.devices.append(address)
                                _LOGGER.info("Discovered Shelly device at %s", address)
                except OSError, RuntimeError:
                    pass
        except OSError, RuntimeError:
            pass
    finally:
        zeroconf.close()
    # Remove duplicates while preserving order
    devices = []
    seen = set()
    for device in listener.devices:
        if device not in seen:
            devices.append(device)
            seen.add(device)
    return devices
