"""Shelly Backup."""

import json
import logging
from pathlib import Path

import httpx

_LOGGER = logging.getLogger(__name__)


class Backup:
    """Shelly Backup."""

    _ip_address: str | None = None
    _target_folder: Path | None = None

    def __init__(self, ip_address: str, target_folder: str):
        """Initialise backup."""
        self._ip_address = ip_address
        if target_folder:
            # Create folder structure if it doesn't exist.
            Path(target_folder).mkdir(parents=True, exist_ok=True)
            self._target_folder = Path(target_folder)
        else:
            self._target_folder = Path.cwd()

    def execute(self):
        """Run device backup."""
        try:
            # Get some basic information from the device to determine which generation
            url: str = f"http://{self._ip_address}/shelly"
            response = httpx.get(url)
            if response.status_code == httpx.codes.OK:
                response_json = response.json()
                _LOGGER.info(response_json)
                # Check for 'gen' tag 2 (with 1 being the default)
                shelly_gen = response_json.get("gen", 1)
                _LOGGER.info("Device identified as generation %s", shelly_gen)
                match shelly_gen:
                    case 1:
                        self._generation_1(response_json)
                    case 2:
                        self._generation_2(response_json)
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

    def _generation_1(self, basic_device_information: dict):
        """Backup generation 1 device."""
        urls: dict = {
            "settings": f"http://{self._ip_address}/settings",
            "actions": f"http://{self._ip_address}/settings/actions",
            "status": f"http://{self._ip_address}/status",
        }
        self._configuration(urls)

    def _generation_2(self, basic_device_information: dict):
        """Backup generation 2 device."""
        urls: dict = {
            "configuration": f"http://{self._ip_address}/rpc/Shelly.GetConfig",
            "device_info": f"http://{self._ip_address}/rpc/Shelly.GetDeviceInfo",
            "status": f"http://{self._ip_address}/rpc/Shelly.GetStatus",
        }
        self._configuration(urls)

    def _configuration(self, urls: dict):
        """Fetch configuration from the provided list of URLs."""
        for information_type, url in urls.items():
            response = httpx.get(url)
            if response.status_code == httpx.codes.OK:
                response_json = response.json()
                self._store(information_type, response_json)
            else:
                _LOGGER.warning(
                    "Unable to get device settings from %s, response code %s",
                    url,
                    response.status_code,
                )

    def _store(self, information_type: str, device_settings: dict):
        """Store device settings."""
        filename: str = f"shelly-{self._ip_address}-{information_type}.json"
        filepath = self._target_folder.joinpath(filename)
        with open(filepath, "w") as file:
            json.dump(device_settings, file, indent=2)
            _LOGGER.info("Configuration stored: %s", filepath)
