# visit-n-sites-and-collect

This module automates visiting N-site's campaign links.

## Requirements

* Python 3.11: This version is verified and required for compatibility.

* Driver Support: As of January 26, 2026, Python 3.11 is necessary to run `undetected-chromedriver` successfully.

## Quick Start Guide

* Install python and uv.

  Ensure that both Python 3.11 and the uv package manager are installed on your system.

* Edit the configuration file: `config/global_config.yaml`.
  Look for `config/global_config.yaml.template`.

* Setup Google Cloud (Optional)

  If you need Google Drive integration:

  * Create a Google Cloud application.

  * Prepare your `google_cloud_credentials.json` file.

  * Refer to `cloud_file_storage.py` for specific implementation details.

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
