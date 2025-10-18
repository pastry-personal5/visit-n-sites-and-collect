# visit-n-sites-and-collect

This module automates visiting N-site's campaign links.

## Requirements

It is verified that it works with Python 3.11.

## Quick Start Guide

* Install python and pip.

  Ensure Python 3.11 (or later) and pip are installed on your system.

* Edit the configuration file: `global_config.yaml`.

* Optionally, create a Google Cloud application for Google Drive access.

  Prepare `google_cloud_credentials.json` file.

  Look for the `cloud_file_storage.py` for details.

* Run the module.

  Execute the script.
  ```bash
  ./1
  ```

## Test

* Run the following command to test.
  ```bash
  make test
  ```
