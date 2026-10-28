# Shelly Backup

[![Build Status](https://github.com/exxamalte/shelly-backup/actions/workflows/tests.yml/badge.svg)](https://github.com/exxamalte/shelly-backup/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/exxamalte/shelly-backup/graph/badge.svg?token=47OELOAUP4)](https://codecov.io/gh/exxamalte/shelly-backup)

Command line tool that fetches the configuration of Shelly devices and stores them in a TinyDB database.
This might be useful if the device loses its configuration for whatever reason. However, restoring settings to the
device is not supported.

* Support for generation 1, 2 and 3 devices.
* Fetches device configuration:
  * Gen 1: Settings, actions and status
  * Gen 2 and Gen 3: Configuration, device info and status
* No support for authenticated access to devices.
* No restore capability.

## Usage

To back up the device configuration of a single Shelly you have to specify the IP address with the `ip-address` option.
The database will be stored in the current folder as `shelly_backup.json`.
```commandline
python -m shelly_backup.cli --ip-address 192.168.10.20
```

You can use the `target_folder` option to store the database into a specific folder.
```commandline
python -m shelly_backup.cli --ip-address 192.168.10.20 --target-folder backup_folder
```

## Configuration file

You can create a YAML configuration file to specify multiple IP addresses of Shelly devices.

```yaml
ip_addresses:
  - 192.168.10.20
  - 192.168.10.21
  - 192.168.10.23
  - 192.168.10.24

target_folder: backup_folder
```

```commandline
python -m shelly_backup.cli --configuration configuration.yaml
```
