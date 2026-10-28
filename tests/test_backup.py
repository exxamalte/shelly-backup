"""Tests for backup module."""

import tempfile
from unittest.mock import Mock, mock_open, patch

import httpx

from shelly_backup.backup import Backup
from shelly_backup.configuration import Configuration


class TestBackup:
    """Test Backup class."""

    def test_execute_no_ip_addresses(self):
        """Test execute when no IP addresses are configured."""
        config = Configuration(None, None, None)
        backup = Backup(config)
        with patch.object(backup, "_device_backup") as mock_device_backup:
            backup.execute()
            mock_device_backup.assert_not_called()

    def test_execute_with_ip_addresses(self):
        """Test execute with IP addresses."""
        config = Configuration("192.168.1.1", None, None)
        # Also test with multiple via a different approach
        backup = Backup(config)
        with (
            patch.object(backup, "_device_backup") as mock_device_backup,
            patch.object(
                config, "ip_addresses", return_value=["192.168.1.1", "192.168.1.2"]
            ),
        ):
            backup.execute()
            assert mock_device_backup.call_count == 2
            mock_device_backup.assert_any_call("192.168.1.1")
            mock_device_backup.assert_any_call("192.168.1.2")

    @patch("httpx.get")
    def test_device_backup_generation_1(self, mock_get):
        """Test device backup for generation 1 device."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)

            mock_response = Mock()
            mock_response.status_code = httpx.codes.OK
            mock_response.json.return_value = {"type": "SHSW-1", "mac": "ABC123"}
            mock_get.return_value = mock_response

            with patch.object(backup, "_generation_1") as mock_gen1:
                backup._device_backup("192.168.1.1")  # noqa: SLF001
                mock_gen1.assert_called_once_with(
                    "192.168.1.1", {"type": "SHSW-1", "mac": "ABC123"}
                )

    @patch("httpx.get")
    def test_device_backup_generation_2(self, mock_get):
        """Test device backup for generation 2 device."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)

            mock_response = Mock()
            mock_response.status_code = httpx.codes.OK
            mock_response.json.return_value = {"gen": 2, "type": "SNSW-001X16EU"}
            mock_get.return_value = mock_response

            with patch.object(backup, "_generation_2") as mock_gen2:
                backup._device_backup("192.168.1.1")  # noqa: SLF001
                mock_gen2.assert_called_once()

    @patch("httpx.get")
    def test_device_backup_generation_3(self, mock_get):
        """Test device backup for generation 3 device."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)

            mock_response = Mock()
            mock_response.status_code = httpx.codes.OK
            mock_response.json.return_value = {"gen": 3, "type": "S3SW-001X16EU"}
            mock_get.return_value = mock_response

            with patch.object(backup, "_generation_2") as mock_gen2:
                backup._device_backup("192.168.1.1")  # noqa: SLF001
                mock_gen2.assert_called_once()

    @patch("httpx.get")
    def test_device_backup_unknown_generation(self, mock_get):
        """Test device backup for unknown generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)

            mock_response = Mock()
            mock_response.status_code = httpx.codes.OK
            mock_response.json.return_value = {"gen": 99}
            mock_get.return_value = mock_response

            with (
                patch.object(backup, "_generation_1") as mock_gen1,
                patch.object(backup, "_generation_2") as mock_gen2,
            ):
                backup._device_backup("192.168.1.1")  # noqa: SLF001
                mock_gen1.assert_not_called()
                mock_gen2.assert_not_called()

    @patch("httpx.get")
    def test_device_backup_http_error_status(self, mock_get):
        """Test device backup when HTTP request fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)

            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            with patch.object(backup, "_generation_1") as mock_gen1:
                backup._device_backup("192.168.1.1")  # noqa: SLF001
                mock_gen1.assert_not_called()

    @patch("httpx.get")
    def test_device_backup_http_exception(self, mock_get):
        """Test device backup when HTTP exception occurs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)
            mock_request = Mock()
            mock_request.url = "http://192.168.1.1/shelly"
            error = httpx.HTTPError("Connection error")
            error.request = mock_request
            mock_get.side_effect = error

            backup._device_backup("192.168.1.1")  # noqa: SLF001

    def test_generation_1_backup(self):
        """Test generation 1 backup process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)
            with (
                patch.object(
                    backup,
                    "_device_configuration",
                    return_value={"settings": {}, "status": {}},
                ) as mock_device_config,
                patch.object(backup, "_store") as mock_store,
            ):
                backup._generation_1("192.168.1.1", {})  # noqa: SLF001

                mock_device_config.assert_called_once()
                call_args = mock_device_config.call_args[0][0]
                assert "settings" in call_args
                assert "actions" in call_args
                assert "status" in call_args
                assert call_args["settings"] == "http://192.168.1.1/settings"
                mock_store.assert_called_once_with(
                    "192.168.1.1", {"settings": {}, "status": {}}
                )

    def test_generation_2_backup(self):
        """Test generation 2 backup process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)
            with (
                patch.object(
                    backup,
                    "_device_configuration",
                    return_value={"configuration": {}, "status": {}},
                ) as mock_device_config,
                patch.object(backup, "_store") as mock_store,
            ):
                backup._generation_2("192.168.1.1", {"gen": 2})  # noqa: SLF001

                mock_device_config.assert_called_once()
                call_args = mock_device_config.call_args[0][0]
                assert "configuration" in call_args
                assert "device_info" in call_args
                assert "status" in call_args
                mock_store.assert_called_once()

    @patch("httpx.get")
    def test_device_configuration(self, mock_get):
        """Test fetching device configuration from multiple URLs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)

            def mock_response_side_effect(url, **kwargs):
                response = Mock()
                if url == "http://192.168.1.1/settings":
                    response.status_code = httpx.codes.OK
                    response.json.return_value = {"wifi": {"ssid": "test"}}
                elif url == "http://192.168.1.1/status":
                    response.status_code = httpx.codes.OK
                    response.json.return_value = {"uptime": 12345}
                else:
                    response.status_code = 404
                return response

            mock_get.side_effect = mock_response_side_effect

            urls = {
                "settings": "http://192.168.1.1/settings",
                "status": "http://192.168.1.1/status",
                "actions": "http://192.168.1.1/settings/actions",
            }
            result = backup._device_configuration(urls)  # noqa: SLF001

            assert result == {
                "settings": {"wifi": {"ssid": "test"}},
                "status": {"uptime": 12345},
            }
            assert mock_get.call_count == 3

    def test_store(self):
        """Test storing device configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Configuration(None, tmpdir, None)
            backup = Backup(config)

            device_settings = {"settings": {"test": "value"}}
            with patch("builtins.open", mock_open()) as mock_file:
                backup._store("192.168.1.1", device_settings)  # noqa: SLF001
                mock_file.assert_called_once()
                call_args = mock_file.call_args[0]
                assert str(call_args[0]).endswith("shelly-192.168.1.1.json")
                assert call_args[1] == "w"
