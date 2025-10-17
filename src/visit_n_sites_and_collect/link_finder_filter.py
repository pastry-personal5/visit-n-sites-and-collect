"""
|LinkFinderFilter| contains a filter logic to filter out campaign URLs.
It's a business logic.
Therefore, a class |LinkFinderFilter| is introduced.
"""
class LinkFinderFilter:
    def __init__(self):
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