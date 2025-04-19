"""Shelly Backup CLI tool."""

import argparse
import importlib.metadata
import logging

from shelly_backup.configuration import Configuration

from .backup import Backup
from .consts import APPLICATION_NAME


def main():
    """Shelly Backup CLI tool."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(
        "%s started (version %s)...",
        APPLICATION_NAME,
        importlib.metadata.version("shelly_backup"),
    )
    # Command line parameters
    parser = argparse.ArgumentParser(description=APPLICATION_NAME)
    parser.add_argument(
        "--ip-address",
        dest="ip_address",
        required=False,
        help="IP address of the Shelly device",
    )
    parser.add_argument(
        "--target",
        dest="target",
        required=False,
        help="Target folder where configuration will be stored",
    )
    parser.add_argument(
        "--configuration",
        dest="configuration_file",
        required=False,
        help="Configuration file",
    )
    args = parser.parse_args()
    try:
        # Set up configuration
        configuration = Configuration(
            args.ip_address, args.target, args.configuration_file
        )
        # Execute backup
        backup = Backup(configuration)
        backup.execute()
    except OSError as e:
        logger.error("Unable to create device backup: %s", e)


if __name__ == "__main__":
    main()
