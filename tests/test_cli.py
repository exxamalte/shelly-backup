"""Tests for CLI module."""

from unittest.mock import Mock, patch

from shelly_backup import cli


class TestCLI:
    """Test CLI module."""

    @patch("shelly_backup.cli.Backup")
    @patch("shelly_backup.cli.Configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_ip_address(
        self, mock_parse_args, mock_configuration, mock_backup
    ):
        """Test main function with IP address argument."""
        mock_args = Mock()
        mock_args.ip_address = "192.168.1.1"
        mock_args.target_folder = None
        mock_args.configuration_file = None
        mock_parse_args.return_value = mock_args

        mock_config_instance = Mock()
        mock_configuration.return_value = mock_config_instance
        mock_backup_instance = Mock()
        mock_backup.return_value = mock_backup_instance

        cli.main()

        mock_configuration.assert_called_once_with("192.168.1.1", None, None)
        mock_backup.assert_called_once_with(mock_config_instance)
        mock_backup_instance.execute.assert_called_once()

    @patch("shelly_backup.cli.Backup")
    @patch("shelly_backup.cli.Configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_configuration_file(
        self, mock_parse_args, mock_configuration, mock_backup
    ):
        """Test main function with configuration file."""
        mock_args = Mock()
        mock_args.ip_address = None
        mock_args.target_folder = None
        mock_args.configuration_file = "config.yaml"
        mock_parse_args.return_value = mock_args

        mock_config_instance = Mock()
        mock_configuration.return_value = mock_config_instance
        mock_backup_instance = Mock()
        mock_backup.return_value = mock_backup_instance

        cli.main()

        mock_configuration.assert_called_once_with(None, None, "config.yaml")
        mock_backup_instance.execute.assert_called_once()

    @patch("shelly_backup.cli.Backup")
    @patch("shelly_backup.cli.Configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_os_error_handling(
        self, mock_parse_args, mock_configuration, mock_backup
    ):
        """Test main function handles OSError."""
        mock_args = Mock()
        mock_args.ip_address = "192.168.1.1"
        mock_args.target_folder = None
        mock_args.configuration_file = None
        mock_parse_args.return_value = mock_args

        mock_configuration.side_effect = OSError("Permission denied")

        # Should not raise exception
        cli.main()
