# Shelly Backup

Command line tool that fetches the configuration of Shelly devices and generates a local backup in JSON format.
This might be useful if the device loses its configuration for whatever reason. However, restoring settings to the
device is not supported.

* Support for generation 1 and 2 devices.
* Fetches device configuration:
  * Gen 1: Settings, actions and status
  * Gen 2: Configuration, device info and status
* No support for authenticated access to devices.
* No restore capability.
