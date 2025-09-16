from src.visit_n_sites_and_collect.article_link_to_campaign_link_cache import (
    ArticleLinkToCampaignLinkCache,
)


class LinkFinderImplBase:

    def __init__(
        self, article_link_to_campaign_link_cache: ArticleLinkToCampaignLinkCache
    ):
        self.article_link_to_campaign_link_cache = article_link_to_campaign_link_cache  # It's a shared object. Let's reference it.

    def cleanup(self) -> None:
        pass

    def is_starting_with_campaign_url(self, campaign_link: str) -> bool:
        if (
            campaign_link.startswith("https://campaign2-api.naver.com/")
            or campaign_link.startswith("https://ofw.adison.co/")
            or campaign_link.startswith("https://campaign2.naver.com/")
            or campaign_link.startswith("https://naver.me/")
        ):
            return True
        return False
