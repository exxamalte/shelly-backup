"""Shelly Backup."""

import json
import logging

import httpx

from .configuration import Configuration

_LOGGER = logging.getLogger(__name__)


class Backup:
    """Shelly Backup."""

    _configuration: Configuration

    def __init__(self, configuration: Configuration):
        """Initialise backup."""
        self._configuration = configuration

    def execute(self):
        """Run device backup."""
        ip_addresses = self._configuration.ip_addresses()
        if not ip_addresses:
            _LOGGER.warning(
                "No IP addresses of Shelly devices specified. Unable to continue."
            )
            return
        for ip_address in ip_addresses:
            self._device_backup(ip_address)

    def _device_backup(self, ip_address: str):
        """Create device backup from Shelly under provided IP address."""
        try:
            # Get some basic information from the device to determine which generation
            url: str = f"http://{ip_address}/shelly"
            response = httpx.get(url)
            if response.status_code == httpx.codes.OK:
                response_json = response.json()
                _LOGGER.debug(response_json)
                # Check for 'gen' tag 2 or 3 (with 1 being the default)
                shelly_gen = response_json.get("gen", 1)
                _LOGGER.info("Device identified as generation %s", shelly_gen)
                match shelly_gen:
                    case 1:
                        self._generation_1(ip_address, response_json)
                    case 2 | 3:
                        self._generation_2(ip_address, response_json)
                    case _:
                        # Unknown generation.
                        _LOGGER.warning("Unknown generation: %s", shelly_gen)
            else:
                _LOGGER.warning(
                    "Unable to get basic device information from %s, response code %s",
                    url,
                    response.status_code,
                )
        except httpx.HTTPError as exc:
            _LOGGER.warning("HTTP Exception for %s - %s", exc.request.url, exc)

    def _generation_1(self, ip_address: str, basic_device_information: dict):
        """Backup generation 1 device."""
        urls: dict = {
            "settings": f"http://{ip_address}/settings",
            "actions": f"http://{ip_address}/settings/actions",
            "status": f"http://{ip_address}/status",
        }
        configuration: dict = self._device_configuration(urls)
        self._store(ip_address, configuration)

    def _generation_2(self, ip_address: str, basic_device_information: dict):
        """Backup generation 2 device."""
        urls: dict = {
            "configuration": f"http://{ip_address}/rpc/Shelly.GetConfig",
            "device_info": f"http://{ip_address}/rpc/Shelly.GetDeviceInfo",
            "status": f"http://{ip_address}/rpc/Shelly.GetStatus",
        }
        configuration: dict = self._device_configuration(urls)
        self._store(ip_address, configuration)

    def _device_configuration(self, urls: dict) -> dict:
        """Fetch device configuration from the provided list of URLs."""
        result: dict = {}
        for information_type, url in urls.items():
            response = httpx.get(url)
            if response.status_code == httpx.codes.OK:
                response_json = response.json()
                result[information_type] = response_json
            else:
                _LOGGER.warning(
                    "Unable to get device settings from %s, response code %s",
                    url,
                    response.status_code,
                )
        return result

    def _store(self, ip_address: str, device_settings: dict):
        """Store device settings."""
        filename: str = f"shelly-{ip_address}.json"
        filepath = self._configuration.target_folder().joinpath(filename)
        with open(filepath, "w") as file:
            json.dump(device_settings, file, indent=2)
            _LOGGER.info("Configuration stored: %s", filepath)
