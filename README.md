# visit-n-sites-and-collect

This module automates visiting N-site's campaign links.

## Requirements

It is verified that it works with Python 3.11.

## Quick Start Guide

* Install python and pip.

  Ensure Python 3.11 (or later) and pip are installed on your system.

* Create a virtual environment.

  Run the following command to create a virtual environment:
  ```bash
  python -m venv venv
  ```

* Activate the virtual environment.

  ```bash
  source 0
  ```

* Install requirements.

  Run the following command to install requirements.
  ```bash
  pip install -r requirements.txt
  ```

* Edit the configuration file: `global_config.yaml`.

* Run the module.

  Execute the script.
  ```bash
  python main.py
  ```

* Optionally, create a Google Cloud application for Google Drive access.

  Prepare `google_cloud_credentials.json` file.

  Look for the `cloud_file_storage.py` for details.

## Test

* Run the following command to test.
  ```bash
  make test
  ```
