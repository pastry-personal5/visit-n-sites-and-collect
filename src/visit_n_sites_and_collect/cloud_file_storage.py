import json
import keyring
import os


from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
from loguru import logger
from google.oauth2.credentials import Credentials


class CloudFileStorage:
    """
    A cloud file storage.
    It's using Google Cloud and Google Cloud Services.
    Prerequisites:
        Set up a Google Cloud project and enable the Google Drive API.
        Download the google_cloud_credentials.json file for OAuth 2.0.
        Install the google-api-python-client, google-auth-httplib2, and google-auth-oauthlib libraries.
    """

    # Scopes for Google Drive API
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    SERVICE_NAME = "google-workspace-quick-tools-v0001"
    TOKEN_KEY = "google-workspace-quick-tools-user-token"

    def __init__(self):
        self.flag_authenticated = False
        self.drive_service = None

    def _load_credentials(self) -> Credentials | None:
        """
        Load stored credentials from the keyring.
        """
        token_json = keyring.get_password(CloudFileStorage.SERVICE_NAME, CloudFileStorage.TOKEN_KEY)
        if token_json:
            creds_data = json.loads(token_json)
            return Credentials.from_authorized_user_info(creds_data, CloudFileStorage.SCOPES)
        return None

    def _save_credentials(self, credentials) -> None:
        creds_json = credentials.to_json()
        keyring.set_password(CloudFileStorage.SERVICE_NAME, CloudFileStorage.TOKEN_KEY, creds_json)

    def _authenticate_google_drive(self) -> Credentials | None:
        """
        Authenticate and create the Google Drive service.
        """
        creds = self._load_credentials()
        if creds and creds.valid:
            self.drive_service = build("drive", "v3", credentials=creds)
            self.flag_authenticated = True
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._save_credentials(creds)
            self.drive_service = build("drive", "v3", credentials=creds)
            self.flag_authenticated = True
            return creds

        const_file_path_for_client_secrets = os.path.join(".", "data", "google_cloud_credentials.json")
        flow = InstalledAppFlow.from_client_secrets_file(const_file_path_for_client_secrets, CloudFileStorage.SCOPES)
        creds = flow.run_local_server(open_browser=True)
        self._save_credentials(creds)

        self.drive_service = build("drive", "v3", credentials=creds)
        self.flag_authenticated = True

        return creds

    def _search_file(self, file_name: str, folder_id=None) -> dict | None:
        """
        Search for a file by name in a specific folder (if provided).
        """
        logger.info(f"Searching for file '{file_name}' in folder '{folder_id}'...")
        query = f"name = '{file_name}' and trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        results = self.drive_service.files().list(q=query, spaces="drive", fields="files(id, name)", pageSize=1).execute()

        files = results.get("files", [])
        return files[0] if files else None

    def _upload_or_update_file(self, file_name: str, file_path: str, folder_id=None) -> dict:
        """
        Upload a new file or update an existing file in Google Drive.
        """
        logger.info(f"Uploading/updating file '{file_name}' with file_path '{file_path}' to folder '{folder_id}'...")
        file_metadata = {"name": file_name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        # Check if the file already exists
        existing_file = self._search_file(file_name, folder_id)

        media = MediaFileUpload(file_path, resumable=True)

        if existing_file:
            # Update the existing file
            file_id = existing_file["id"]
            updated_file = self.drive_service.files().update(fileId=file_id, media_body=media).execute()
            logger.info(f"File '{file_name}' updated successfully.")
            return updated_file

        # Upload a new file
        new_file = self.drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        logger.info(f"File '{file_name}' uploaded successfully.")
        return new_file

    def _download_file(self, file_id: str, file_path: str) -> None:
        """
        Download a file from Google Drive.
        """
        request = self.drive_service.files().get_media(fileId=file_id)

        with open(file_path, "wb") as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}% complete.")

        logger.info(f"File downloaded to: {file_path}")

    def upload(self, file_name: str, file_path: str, folder_id_for_parent_of_cloud_file_storage: str) -> bool:
        if not self.flag_authenticated:
            self._authenticate_google_drive()
        if not self.flag_authenticated:
            return False
        assert self.drive_service is not None

        self._upload_or_update_file(file_name, file_path, folder_id=folder_id_for_parent_of_cloud_file_storage)
        return True

    def download(self, file_name: str, file_path: str, folder_id_for_parent_of_cloud_file_storage: str) -> bool:
        if not self.flag_authenticated:
            self._authenticate_google_drive()
        if not self.flag_authenticated:
            return False
        # Check if the file exists
        existing_file = self._search_file(file_name, folder_id=folder_id_for_parent_of_cloud_file_storage)
        if not existing_file:
            return False
        file_id = existing_file["id"]
        self._download_file(file_id, file_path)
        return True

    def delete(self, file_name: str, folder_id_for_parent_of_cloud_file_storage: str) -> bool:
        if not self.flag_authenticated:
            self._authenticate_google_drive()
        if not self.flag_authenticated:
            return False
        # Check if the file exists
        existing_file = self._search_file(file_name, folder_id=folder_id_for_parent_of_cloud_file_storage)
        if not existing_file:
            return False
        file_id = existing_file["id"]
        self.drive_service.files().delete(fileId=file_id).execute()
        logger.info(f"File '{file_name}' deleted successfully.")
        return True

    def authenticate_google_drive(self) -> None:
        """
        Public method to authenticate Google Drive.
        """
        self._authenticate_google_drive()
