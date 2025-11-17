import unittest
from unittest.mock import MagicMock, mock_open, patch

from visit_n_sites_and_collect.cloud_file_storage import CloudFileStorage


class CloudFileStorageTestCase(unittest.TestCase):
    def setUp(self):
        self.storage = CloudFileStorage()
        self.storage.drive_service = MagicMock()
        self.storage.flag_authenticated = True

    def test_search_file_with_parent_returns_first_match(self):
        files_api = self.storage.drive_service.files.return_value
        list_call = files_api.list.return_value
        expected_file = {"id": "123", "name": "document.txt"}
        list_call.execute.return_value = {"files": [expected_file]}

        result = self.storage._search_file("document.txt", folder_id="folder-42")

        files_api.list.assert_called_once_with(
            q="name = 'document.txt' and trashed = false and 'folder-42' in parents",
            spaces="drive",
            fields="files(id, name)",
            pageSize=1,
        )
        self.assertEqual(expected_file, result)

    def test_search_file_without_results_returns_none(self):
        files_api = self.storage.drive_service.files.return_value
        files_api.list.return_value.execute.return_value = {"files": []}

        result = self.storage._search_file("missing.txt")

        self.assertIsNone(result)

    @patch("visit_n_sites_and_collect.cloud_file_storage.MediaFileUpload")
    def test_upload_or_update_updates_existing_file(self, media_upload_cls):
        with patch.object(self.storage, "_search_file", return_value={"id": "existing-id"}) as search_mock:
            update_call = self.storage.drive_service.files.return_value.update.return_value
            update_call.execute.return_value = {"id": "existing-id"}

            response = self.storage._upload_or_update_file("report.csv", "/tmp/report.csv", folder_id="folder-1")

        media_upload_cls.assert_called_once_with("/tmp/report.csv", resumable=True)
        search_mock.assert_called_once_with("report.csv", "folder-1")
        self.storage.drive_service.files.return_value.update.assert_called_once_with(
            fileId="existing-id", media_body=media_upload_cls.return_value
        )
        update_call.execute.assert_called_once_with()
        self.assertEqual({"id": "existing-id"}, response)

    @patch("visit_n_sites_and_collect.cloud_file_storage.MediaFileUpload")
    def test_upload_or_update_creates_new_file(self, media_upload_cls):
        with patch.object(self.storage, "_search_file", return_value=None) as search_mock:
            create_call = self.storage.drive_service.files.return_value.create.return_value
            create_call.execute.return_value = {"id": "new-id"}

            response = self.storage._upload_or_update_file("report.csv", "/tmp/report.csv")

        media_upload_cls.assert_called_once_with("/tmp/report.csv", resumable=True)
        search_mock.assert_called_once_with("report.csv", None)
        self.storage.drive_service.files.return_value.create.assert_called_once_with(
            body={"name": "report.csv"},
            media_body=media_upload_cls.return_value,
            fields="id",
        )
        create_call.execute.assert_called_once_with()
        self.assertEqual({"id": "new-id"}, response)


if __name__ == "__main__":
    unittest.main()
