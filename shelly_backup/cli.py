"""Shelly Backup CLI tool."""
import argparse
import importlib.metadata
import logging

from .consts import APPLICATION_NAME
from .backup import Backup


def main():
    """Shelly Backup CLI tool."""
    logging.basicConfig(
        level=logging.INFO,
    )
    logger = logging.getLogger(__name__)
    logger.info("%s started (version %s)...",
                APPLICATION_NAME, importlib.metadata.version("shelly_backup"))

    parser = argparse.ArgumentParser(description='Shelly Backup')
    parser.add_argument('--ip-address', dest='ip_address', required=True, help='IP address of the Shelly device')
    args = parser.parse_args()
    # Execute backup
    backup = Backup(args.ip_address)
    backup.execute()


if __name__ == "__main__":
    main()
