#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from loguru import logger

from global_config import read_global_config

from cloud_file_storage import CloudFileStorage
from configuration_for_cloud_file_storage import ConfigurationForCloudFileStorage
from link_visitor import VisitedCampaignLinkController


class CleaningController:
    """
    A controller to clean the visited URLs file.
    It uses the CloudFileStorage and VisitedCampaignLinkController classes to manage the visited URLs.
    """

    def __init__(self):
        self.cloud_file_storage = CloudFileStorage()
        self.visited_campaign_link_controller = VisitedCampaignLinkController()
        configuration_for_cloud_file_storage = None

    def delete_all(self, global_config: dict) -> None:
        if "cloud_file_storage" in global_config:
            global_config_for_cloud_file_storage = global_config["cloud_file_storage"]
            if "folder_id_for_parent" in global_config_for_cloud_file_storage:
                self.configuration_for_cloud_file_storage = ConfigurationForCloudFileStorage()
                self.configuration_for_cloud_file_storage.init_with_core_config(global_config_for_cloud_file_storage["folder_id_for_parent"])
        self.visited_campaign_link_controller.init_with_cloud_file_storage(self.configuration_for_cloud_file_storage, self.cloud_file_storage)

        users = global_config["users"]
        for user in users:
            nid = user["id"]
            logger.info(f"Starting cleanup for user ID: {nid}")
            self.visited_campaign_link_controller.reset_with_nid(nid)
            self.visited_campaign_link_controller.delete_all()
            logger.info(f"Cleanup completed for user ID: {nid}")

def main():
    """
    Main function to clean the visited URLs file.
    """
    # Read the global configuration
    global_config = read_global_config()
    if not global_config:
        logger.error("Failed to read global configuration.")
        return

    cleaning_controller = CleaningController()
    cleaning_controller.delete_all(global_config)


if __name__ == "__main__":
    main()
