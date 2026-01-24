#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script is used to clean the visited URLs file.
It uses the CloudFileStorage and VisitedCampaignLinkController classes to manage the visited URLs.
It can be run from the command line and takes no arguments.
It reads the global configuration from a file and uses it to initialize the CloudFileStorage and VisitedCampaignLinkController classes.
"""

from loguru import logger

from src.visit_n_sites_and_collect.global_config import GlobalConfigController, GlobalConfigIR

from src.visit_n_sites_and_collect.cloud_file_storage import CloudFileStorage
from src.visit_n_sites_and_collect.configuration_for_cloud_file_storage import ConfigurationForCloudFileStorage
from src.visit_n_sites_and_collect.link_visitor import VisitedCampaignLinkController


class CleaningController:
    """
    A controller to clean the visited URLs file.
    It uses the CloudFileStorage and VisitedCampaignLinkController classes to manage the visited URLs.
    It provides functionality to delete all visited URLs for a given user.
    """

    def __init__(self):
        self.cloud_file_storage = CloudFileStorage()
        self.visited_campaign_link_controller = VisitedCampaignLinkController()
        self.configuration_for_cloud_file_storage = None

    def delete_all(self, global_config_ir: GlobalConfigIR) -> None:
        global_config = global_config_ir.config
        if "cloud_file_storage" in global_config:
            global_config_for_cloud_file_storage = global_config["cloud_file_storage"]
            if "enabled" in global_config_for_cloud_file_storage:
                if "folder_id_for_parent" in global_config_for_cloud_file_storage:
                    self.configuration_for_cloud_file_storage = ConfigurationForCloudFileStorage()
                    self.configuration_for_cloud_file_storage.init_with_core_config(global_config_for_cloud_file_storage["folder_id_for_parent"])
                    self.visited_campaign_link_controller.flag_use_cloud_file_storage = True
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
    global_config_controller = GlobalConfigController()
    global_config_ir = global_config_controller.read_global_config()
    if not global_config_ir:
        logger.error("Failed to read global configuration.")
        return

    cleaning_controller = CleaningController()
    cleaning_controller.delete_all(global_config_ir)


if __name__ == "__main__":
    main()
