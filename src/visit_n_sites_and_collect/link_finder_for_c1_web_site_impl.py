from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger
import requests

from link_finder_impl_base import LinkFinderImplBase
import publisher


class LinkFinderForC1WebSiteImpl(LinkFinderImplBase):

    def get_publisher_meta(self):
        target_base_url_list = [
            # The base URL to start with
            "https://www.clien.net/service/board/jirum",
            "https://www.clien.net/service/board/park",
        ]

        template_list = [
            "https://www.clien.net/service/board/jirum?&od=T31&category=0&po=%d",
            "https://www.clien.net/service/board/park?&od=T31&category=0&po=%d",
        ]
        return (target_base_url_list, template_list)

    def find_set_of_campaign_links(self, days_difference_since_last_run: int) -> set[str]:
        set_of_campaign_links = set()
        (target_base_url_list, template_list) = self.get_publisher_meta()
        publisher_links_to_visit = publisher.create_publisher_links_to_visit(target_base_url_list, template_list, days_difference_since_last_run)
        for publisher_link in publisher_links_to_visit:
            campaign_links = self.find_campaign_links(publisher_link)
            set_of_campaign_links.update(campaign_links)
        logger.info(f"Finally, got ({len(set_of_campaign_links)}) of campaign links.")
        return set_of_campaign_links

    def find_campaign_links(self, publisher_link: str):
        # Initialize a list to store campaign links
        campaign_links = []

        logger.info(f"Visiting ({publisher_link})...")

        # Send a request to the |publisher_link|
        try:
            response = requests.get(publisher_link)
        except requests.exceptions.ConnectionError:
            return []
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all <span> elements with class 'list_subject' and get 'a' tags
        list_of_article_elements = soup.find_all("span", class_="list_subject")
        partial_article_links = []
        for span in list_of_article_elements:
            a_tag = span.find("a", href=True)
            if a_tag and "네이버" in a_tag.text:
                partial_article_links.append(a_tag["href"])

        # Check each Naver link
        for partial_article_link in partial_article_links:
            article_link = urljoin(publisher_link, partial_article_link)

            # It looks up an entry in the cache, first.
            campaign_links = self.article_link_to_campaign_link_cache.get(article_link)
            if campaign_links:
                logger.info(f"Cache hit. Now returning entries from the cache. ({article_link})")
                return campaign_links

            logger.info(f"Visiting ({article_link})...")
            campaign_links = []
            try:
                res = requests.get(article_link)
            except requests.exceptions.ConnectionError:
                logger.warning(f"Could not get the link: ({article_link}). Continue...")
                continue
            inner_soup = BeautifulSoup(res.text, "html.parser")

            # Find all links that start with the campaign URL
            for a_tag in inner_soup.find_all("a", href=True):
                campaign_link = a_tag["href"]
                if self.is_starting_with_campaign_url(campaign_link):
                    campaign_links.append(campaign_link)
                else:
                    # Log only significant links.
                    # We don't want to log all links, because there are too many of them.
                    if campaign_link.find("http") != -1 and campaign_link.find("clien") == -1:
                        logger.info(f"Not a campaign link: {campaign_link}")

            # Note: The length of |campaign_links| can be zero. It's intentional.
            self.article_link_to_campaign_link_cache.put(article_link, campaign_links)

        logger.info(f"Got ({len(campaign_links)}) of campaign links.")

        return campaign_links
