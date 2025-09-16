import os
import pickle

from googleapiclient.discovery import build
from googleapiclient.errors import UnknownApiNameOrVersion
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.exceptions import MutualTLSChannelError, RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from loguru import logger


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

    def __init__(self):
        self.flag_authenticated = False
        self.drive_service = None

    def _authenticate_google_drive(self):
        """
        Authenticate and return a Google Drive service instance.
        """
        const_token_file_path = "google_cloud_token.pickle"
        const_creds_file_path = "google_cloud_credentials.json"

        creds = None
        # Token.pickle stores the user's credentials
        if os.path.exists(const_token_file_path):
            with open(const_token_file_path, "rb") as token:
                creds = pickle.load(token)
        # If there are no valid credentials, prompt the user to log in
        if not creds or not creds.valid:
            flag_has_to_get_creds = True
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    flag_has_to_get_creds = False
                except RefreshError as e:
                    logger.warning("A token refresh error occurred. Please authenticate with a Google ID.")
                    logger.warning(e)
                    flag_has_to_get_creds = True
            else:
                flag_has_to_get_creds = True
            if flag_has_to_get_creds:
                flow = InstalledAppFlow.from_client_secrets_file(const_creds_file_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(const_token_file_path, "wb") as token:
                pickle.dump(creds, token)
        try:
            self.drive_service = build("drive", "v3", credentials=creds)
            self.flag_authenticated = True
        except UnknownApiNameOrVersion as e:
            logger.error("Unknown API name or version.")
            logger.error(e)
        except MutualTLSChannelError as e:
            logger.error("Mutual TLS Channel Error.")
            logger.error(e)

    def _search_file(self, file_name: str, folder_id=None):
        """
        Search for a file by name in a specific folder (if provided).
        """
        query = f"name = '{file_name}' and trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        results = self.drive_service.files().list(q=query, spaces="drive", fields="files(id, name)", pageSize=1).execute()

        files = results.get("files", [])
        return files[0] if files else None

    def _upload_or_update_file(self, file_name: str, file_path: str, folder_id=None):
        """
        Upload a new file or update an existing file in Google Drive.
        """
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

    def _download_file(self, file_id: str, file_name: str) -> None:
        """
        Download a file from Google Drive.
        """
        request = self.drive_service.files().get_media(fileId=file_id)
        file_path = os.path.join(os.getcwd(), file_name)

        with open(file_path, "wb") as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}% complete.")

        logger.info(f"File downloaded to: {file_path}")

    def upload(self, file_name: str, folder_id_for_parent_of_cloud_file_storage: str) -> None:
        if not self.flag_authenticated:
            self._authenticate_google_drive()
        if not self.flag_authenticated:
            return False
        assert self.drive_service is not None

        self._upload_or_update_file(file_name, file_name, folder_id=folder_id_for_parent_of_cloud_file_storage)

    def download(self, file_name: str, folder_id_for_parent_of_cloud_file_storage: str) -> bool:
        if not self.flag_authenticated:
            self._authenticate_google_drive()
        if not self.flag_authenticated:
            return False
        # Check if the file exists
        existing_file = self._search_file(file_name, folder_id=folder_id_for_parent_of_cloud_file_storage)
        if not existing_file:
            return False
        file_id = existing_file["id"]
        self._download_file(file_id, file_name)
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
