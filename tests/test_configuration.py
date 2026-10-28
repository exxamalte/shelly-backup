"""Tests for configuration module."""

from pathlib import Path
import tempfile

import yaml

from shelly_backup.configuration import Configuration


class TestConfiguration:
    """Test Configuration class."""

    def test_init_without_config_file(self):
        """Test initialization without configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = Path(tmpdir) / "backup"
            config = Configuration("192.168.1.1", str(backup_path), None)
            assert config.ip_addresses() == ["192.168.1.1"]
            assert config.target_folder() == Path(str(backup_path))

    def test_init_with_config_file(self):
        """Test initialization with configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {
                "ip_addresses": ["192.168.1.1", "192.168.1.2"],
                "target_folder": str(Path(tmpdir) / "backup"),
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            config = Configuration(None, None, str(config_file))
            assert config.ip_addresses() == ["192.168.1.1", "192.168.1.2"]

    def test_ip_addresses_from_config_file(self):
        """Test getting IP addresses from configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {"ip_addresses": ["192.168.1.1", "192.168.1.2"]}
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            config = Configuration(None, None, str(config_file))
            assert config.ip_addresses() == ["192.168.1.1", "192.168.1.2"]

    def test_ip_addresses_from_ip_address_param(self):
        """Test getting IP addresses from ip_address parameter."""
        config = Configuration("192.168.1.100", None, None)
        assert config.ip_addresses() == ["192.168.1.100"]

    def test_ip_addresses_priority_config_over_param(self):
        """Test that configuration file takes priority over ip_address parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_data = {"ip_addresses": ["192.168.1.1", "192.168.1.2"]}
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            config = Configuration("192.168.1.100", None, str(config_file))
            assert config.ip_addresses() == ["192.168.1.1", "192.168.1.2"]

    def test_ip_addresses_none_when_not_specified(self):
        """Test ip_addresses returns None when nothing specified."""
        config = Configuration(None, None, None)
        assert config.ip_addresses() is None

    def test_target_folder_from_config_file(self):
        """Test getting target folder from configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            backup_dir = Path(tmpdir) / "backup"
            config_data = {"target_folder": str(backup_dir)}
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            config = Configuration(None, None, str(config_file))
            result = config.target_folder()
            assert result == backup_dir

    def test_target_folder_from_param(self):
        """Test getting target folder from parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / "my" / "backup"
            config = Configuration(None, str(backup_dir), None)
            result = config.target_folder()
            assert result == backup_dir

    def test_target_folder_priority_config_over_param(self):
        """Test that configuration file takes priority over parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_dir = Path(tmpdir) / "config"
            param_dir = Path(tmpdir) / "param"
            config_data = {"target_folder": str(config_dir)}
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            config = Configuration(None, str(param_dir), str(config_file))
            result = config.target_folder()
            assert result == config_dir

    def test_target_folder_default_to_cwd(self):
        """Test target folder defaults to current working directory."""
        config = Configuration(None, None, None)
        result = config.target_folder()
        assert result == Path.cwd()
