import os
import uuid

import pytest

from visit_n_sites_and_collect.cloud_file_storage import CloudFileStorage
from visit_n_sites_and_collect.global_config import GlobalConfigController


def _get_cloud_folder_id() -> str | None:
    global_config_ir = GlobalConfigController().read_global_config()
    cloud_config = global_config_ir.raw_config.get("cloud_file_storage", {})
    if not cloud_config.get("enabled"):
        return None
    return cloud_config.get("folder_id_for_parent")


def test_upload_download_and_delete(tmp_path, monkeypatch):
    if os.environ.get("RUN_CLOUD_STORAGE_TESTS") != "1":
        pytest.skip("Set RUN_CLOUD_STORAGE_TESTS=1 to enable Google Drive regression tests.")

    folder_id = _get_cloud_folder_id()
    if not folder_id:
        pytest.skip("No cloud_file_storage.folder_id_for_parent configured.")

    monkeypatch.chdir(tmp_path)
    cloud_file_storage = CloudFileStorage()
    cloud_file_storage.authenticate_google_drive()

    file_name = f"cloud_storage_test_{uuid.uuid4().hex}.txt"
    file_path = tmp_path / file_name
    expected_content = f"This is a test file for cloud storage. {uuid.uuid4().hex}"
    file_path.write_text(expected_content, encoding="utf-8")

    assert cloud_file_storage.upload(file_name, str(file_path), folder_id) is True

    # Remove local file to ensure download repopulates it.
    file_path.unlink()
    assert not file_path.exists()

    assert cloud_file_storage.download(file_name, str(file_path), folder_id) is True
    assert file_path.read_text(encoding="utf-8") == expected_content
    assert cloud_file_storage.delete(file_name, folder_id) is True
