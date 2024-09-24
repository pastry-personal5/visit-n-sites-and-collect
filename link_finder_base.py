from article_link_to_campaign_link_cache import ArticleLinkToCampaignLinkCache


class LinkFinderBase:

    def __init__(self, article_link_to_campaign_link_cache: ArticleLinkToCampaignLinkCache):
        self.article_link_to_campaign_link_cache = article_link_to_campaign_link_cache  # It's a shared object. Let's reference it.
