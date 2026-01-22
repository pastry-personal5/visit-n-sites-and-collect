"""
|LinkFinderFilter| contains a filter logic to filter out campaign URLs.
It's a business logic.
Therefore, a class |LinkFinderFilter| is introduced.
"""
from typing import List


class LinkFinderFilter:
    def __init__(self):
        self.flag_initialized = False
        self.list_of_campaign_link_prefix = None

    def initialize_with_config(self, list_of_campaign_link_prefix: List[str]) -> None:
        self.flag_initialized = True
        self.list_of_campaign_link_prefix = list_of_campaign_link_prefix.copy()

    def is_starting_with_campaign_url(self, campaign_link: str) -> bool:
        if not self.flag_initialized:
            raise RuntimeError("LinkFinderFilter is not initialized yet.")
        for prefix in self.list_of_campaign_link_prefix:
            if campaign_link.startswith(prefix):
                return True
        return False
