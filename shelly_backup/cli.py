"""Shelly Backup CLI tool."""

import argparse
import importlib.metadata
import logging

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
        required=True,
        help="IP address of the Shelly device",
    )
    parser.add_argument(
        "--target",
        dest="target",
        required=False,
        help="Target folder where configuration will be stored",
    )
    args = parser.parse_args()
    try:
        # Execute backup
        backup = Backup(args.ip_address, args.target)
        backup.execute()
    except OSError as e:
        logger.error("Unable to create device backup: %s", e)


if __name__ == "__main__":
    main()
