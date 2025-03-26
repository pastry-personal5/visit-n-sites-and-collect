class ArticleLinkToCampaignLinkCache:

    def __init__(self):
        self.cache = {}

    def put(self, article_link: str, campaign_links: list[str]) -> None:
        # Just overwrite
        self.cache[article_link] = campaign_links

    def get(self, article_link: str):
        if article_link in self.cache:
            return self.cache[article_link]
        return None
