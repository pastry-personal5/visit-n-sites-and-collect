"""
This file contains the class ConfigurationForCloudFileStorage.
"""
class ConfigurationForCloudFileStorage:
    def __init__(self):
        """
        Initialize the class.
        """
        self.flag_has_valid_cloud_file_storage_config = False
        self.folder_id_of_parent_of_cloud_file_storage = None

    def init_with_core_config(self, folder_id_of_parent_of_cloud_file_storage: str) -> None:
        """
        Initialize the class with the given folder_id_of_parent_of_cloud_file_storage.
        """
        self.flag_has_valid_cloud_file_storage_config = True
        self.folder_id_of_parent_of_cloud_file_storage = folder_id_of_parent_of_cloud_file_storage

    def has_valid_cloud_file_storage_config(self) -> bool:
        """
        Return True if the class has a valid cloud file storage configuration.
        """
        return self.flag_has_valid_cloud_file_storage_config