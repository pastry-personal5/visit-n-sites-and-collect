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
from last_run_recorder import LastRunRecorder
from link_finder_for_c1_web_site_impl import LinkFinderForC1WebSiteImpl
from link_finder_for_d1_web_site_impl import LinkFinderForD1WebSiteImpl
from link_visitor import LinkVisitor


class LinkFinderFactory:

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
            return LinkFinderForC1WebSiteImpl(article_link_to_campaign_link_cache)
        if visitor_type == self.const_d1:
            return LinkFinderForD1WebSiteImpl(article_link_to_campaign_link_cache)
        else:
            return None


class MainController:

    def __init__(self):
        self.article_link_to_campaign_link_cache = ArticleLinkToCampaignLinkCache()
        self.link_visitor = LinkVisitor()
        self.link_finders = []

        # Now one has just two link finder objects. Therefore, `self.link_finders`` is going to get two elements.
        link_finder_creator = LinkFinderFactory()
        c1_link_finder = link_finder_creator.build_link_finder(LinkFinderFactory.const_c1, self.article_link_to_campaign_link_cache)
        d1_link_finder = link_finder_creator.build_link_finder(LinkFinderFactory.const_d1, self.article_link_to_campaign_link_cache)
        self.link_finders.append(c1_link_finder)
        self.link_finders.append(d1_link_finder)

    def find_and_visit_all_with_global_config(self, global_config: dict):
        self._init_with_global_config(global_config)
        # This method is a main entry point.
        users = global_config["users"]
        for user in users:
            nid = user["id"]
            npw = user["pw"]
            # (1) Let's find.
            set_of_campaign_links = self._find_all(nid)
            # (2) Let's visit.
            self._visit_all(nid, npw, set_of_campaign_links)

    def _init_with_global_config(self, global_config: dict):
        self.link_visitor.init_with_global_config(global_config)

    def _find_all(self, nid) -> set[str]:
        days_difference_since_last_run = self._get_days_difference_since_last_run(nid)

        # Union all using |update| method of |set|
        set_of_campaign_links = set()
        for link_finder in self.link_finders:
            # Look for |LinkFinderForC1WebSite.find_set_of_campaign_links| as an example...
            result = link_finder.find_set_of_campaign_links(days_difference_since_last_run)
            if result:
                set_of_campaign_links.update(result)
        return set_of_campaign_links

    def _visit_all(self, nid, npw, set_of_campaign_links: set[str]) -> None:
        self.link_visitor.visit_all(nid, npw, set_of_campaign_links)

    def _get_days_difference_since_last_run(self, nid: str) -> int:
        """It returns the number of days since the last run.

        Args:
            nid (str): n-site ID as a string.

        Returns:
            int: The number of days as an integer.
                One returns -1 if the date of the last run is unavailable.
        """
        last_run_recorder = LastRunRecorder()
        date_of_last_run = last_run_recorder.read_date_of_last_run(nid)
        if date_of_last_run != -1:
            today = datetime.date.today()
            days = (today - date_of_last_run).days
            return days
        return -1


def read_global_config() -> dict:
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


def main() -> None:
    main_controller = MainController()
    global_config = read_global_config()
    if not global_config:
        logger.error("The config file is not valid.")
        sys.exit(-1)

    main_controller.find_and_visit_all_with_global_config(global_config)


if __name__ == "__main__":
    main()
