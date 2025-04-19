"""Configuration."""

from pathlib import Path

import yaml


class Configuration:
    """Configuration."""

    _configuration: dict | None = None
    _ip_address: str | None = None
    _target_folder: str | None = None

    def __init__(self, ip_address: str, target_folder: str, configuration_file: str):
        """Initialise backup."""
        if configuration_file:
            with open(configuration_file) as f:
                self._configuration = yaml.load(f, Loader=yaml.FullLoader)
        self._ip_address = ip_address
        self._target_folder = target_folder

    def ip_addresses(self) -> list[str] | None:
        """Get IP addresses from configuration."""
        if self._configuration and "ip_addresses" in self._configuration:
            return self._configuration["ip_addresses"]
        if self._ip_address:
            return [self._ip_address]
        return None

    def target_folder(self) -> Path:
        """Get the target folder from configuration."""
        target_folder: str | None = None
        if self._configuration and "target_folder" in self._configuration:
            target_folder = self._configuration["target_folder"]
        elif self._target_folder:
            target_folder = self._target_folder
        if target_folder:
            # Create folder structure if it doesn't exist.
            Path(target_folder).mkdir(parents=True, exist_ok=True)
            return Path(target_folder)
        return Path.cwd()
