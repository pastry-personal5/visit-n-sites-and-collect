from src.visit_n_sites_and_collect.article_link_to_campaign_link_cache import (
    ArticleLinkToCampaignLinkCache,
)
from src.visit_n_sites_and_collect.link_finder_filter import LinkFinderFilter

class LinkFinderImplBase:

    def __init__(
        self, article_link_to_campaign_link_cache: ArticleLinkToCampaignLinkCache
    ):
        self.article_link_to_campaign_link_cache = article_link_to_campaign_link_cache  # It's a shared object. Let's reference it.
        self.link_finder_filter = LinkFinderFilter()

    def cleanup(self) -> None:
        pass

    def is_starting_with_campaign_url(self, campaign_link: str) -> bool:
        return self.link_finder_filter.is_starting_with_campaign_url(campaign_link)
