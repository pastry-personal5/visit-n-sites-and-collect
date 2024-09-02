from bs4 import BeautifulSoup
import requests

from article_link_to_campaign_link_cache import ArticleLinkToCampaignLinkCache
from link_finder_base import LinkFinderBase

class LinkFinderForD1WebSite(LinkFinderBase):

    def find_set_of_campaign_links(self, days_difference_since_last_run: int):
        return None
