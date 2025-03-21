"""
This module visits Naver Pay's advertisement sites or campaign links.
And it collects a small amount of money.
The source code is derived from an article in https://www.clien.net.
The original author is unknown.
Please visit and find the original author. i.e. https://www.clien.net/service/board/kin/18490638
Please look for `LICENSE` file for license.
Please beware of file encoding.
"""

import datetime
import pprint
import sys

from loguru import logger
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from article_link_to_campaign_link_cache import ArticleLinkToCampaignLinkCache
from link_finder_for_c1_web_site import LinkFinderForC1WebSite
from link_finder_for_d1_web_site import LinkFinderForD1WebSite
from link_visitor import LinkVisitor
from meta_info_manager import SharedContext
import meta_info_manager


class LinkFinderCreator:

    const_c1 = 0
    const_d1 = 1

    def __init__(self):
        pass

    def build_link_finder(
        self,
        visitor_type: int,
        article_link_to_campaign_link_cache: ArticleLinkToCampaignLinkCache,
    ):
        if visitor_type == self.const_c1:
            return LinkFinderForC1WebSite(article_link_to_campaign_link_cache)
        if visitor_type == self.const_d1:
            return LinkFinderForD1WebSite(article_link_to_campaign_link_cache)
        else:
            return None


class MainController:

    def __init__(self):
        self.shared_context = SharedContext()

        self.article_link_to_campaign_link_cache = ArticleLinkToCampaignLinkCache()
        self.link_visitor = LinkVisitor()
        self.link_finders = []

        # Now one has just two link finder objects. Therefore, `self.link_finders`` is going to get two elements.
        link_finder_creator = LinkFinderCreator()
        c1_link_finder = link_finder_creator.build_link_finder(LinkFinderCreator.const_c1, self.article_link_to_campaign_link_cache)
        d1_link_finder = link_finder_creator.build_link_finder(LinkFinderCreator.const_d1, self.article_link_to_campaign_link_cache)
        self.link_finders.append(c1_link_finder)
        self.link_finders.append(d1_link_finder)

    def _init_with_global_config(self, global_config: dict):
        flag_init = False
        # Initialize `self.shared_context`
        if "cloud_file_storage" in global_config:
            global_config_for_cloud_file_storage = global_config["cloud_file_storage"]
            if "folder_id_for_parent" in global_config_for_cloud_file_storage:
                self.shared_context.init_with_core_config(global_config_for_cloud_file_storage["folder_id_for_parent"])
                flag_init = True
        if not flag_init:
            logger.warning("Invalid configuration has been found. Look for main configuration file.")

    def find_and_visit_all_with_global_config(self, global_config: dict):
        self._init_with_global_config(global_config)
        # This method is a main entry point.
        users = global_config["users"]
        for user in users:
            nid = user["id"]
            npw = user["pw"]
            # Let's find.
            set_of_campaign_links = self.find_all(nid)
            # Let's visit.
            self.visit_all(nid, npw, set_of_campaign_links)

    def find_all(self, nid) -> set[str]:
        days_difference_since_last_run = self.get_days_difference_since_last_run(nid)

        # Union all using |update| method of |set|
        set_of_campaign_links = set()
        for link_finder in self.link_finders:
            # Look for |LinkFinderForC1WebSite.find_set_of_campaign_links| as an example...
            result = link_finder.find_set_of_campaign_links(days_difference_since_last_run)
            if result:
                set_of_campaign_links.update(result)
        return set_of_campaign_links

    def visit_all(self, nid, npw, set_of_campaign_links: set[str]) -> None:
        self.link_visitor.visit_all(nid, npw, set_of_campaign_links, self.shared_context)

    def get_days_difference_since_last_run(self, nid: str) -> int:
        """It returns the number of days since the last run.

        Args:
            nid (str): n-site ID as a string.

        Returns:
            int: The number of days as an integer.
                One returns -1 if the date of the last run is unavailable.
        """
        current_meta_info_manager = meta_info_manager.MetaInfoManager(nid, self.shared_context)
        date_of_last_run = current_meta_info_manager.read_date_of_last_run()
        if date_of_last_run != -1:
            today = datetime.date.today()
            days = (today - date_of_last_run).days
            return days
        return -1


def read_global_config():
    """Read a global configuration.

    Returns:
        dict: a user configuration dictionary.
            Currently, its format is YAML and it looks like this below.
            Please note that two spaces are recommended.

            users:
                - id:
                    foo
                pw:
                    bar
                ...
    """
    config_file_path = "./global_config.yaml"
    try:
        f = open(config_file_path, "r", encoding="utf-8")
        global_config = yaml.load(f.read(), Loader=Loader)
    except IOError:
        logger.error(f"Could not read file: {config_file_path}")
        return {}
    return global_config


def main():
    main_controller = MainController()
    global_config = read_global_config()
    if not global_config:
        logger.error("The config file is not valid.")
        sys.exit(-1)

    main_controller.find_and_visit_all_with_global_config(global_config)


if __name__ == "__main__":
    main()
