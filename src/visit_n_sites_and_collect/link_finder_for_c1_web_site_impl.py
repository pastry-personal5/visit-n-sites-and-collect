import time
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger
import requests
import selenium

from visit_n_sites_and_collect.link_finder_impl_base import LinkFinderImplBase
from visit_n_sites_and_collect.publisher import PublisherController
from visit_n_sites_and_collect.article_link_to_campaign_link_cache import (
    ArticleLinkToCampaignLinkCache,
)
from visit_n_sites_and_collect.web_browser_client import WebBrowserClient


class LinkFinderForC1WebSiteImpl(LinkFinderImplBase):

    def __init__(self, article_link_to_campaign_link_cache: ArticleLinkToCampaignLinkCache):
        super().__init__(article_link_to_campaign_link_cache)
        self.web_browser_client = WebBrowserClient()
        self.web_browser_client.prepare()

    def cleanup(self) -> None:
        self.web_browser_client.cleanup()

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
        publisher_controller = PublisherController()
        publisher_links_to_visit = publisher_controller.create_publisher_links_to_visit(target_base_url_list, template_list, days_difference_since_last_run)
        for publisher_link in publisher_links_to_visit:
            campaign_links = self._find_campaign_links(publisher_link)
            set_of_campaign_links.update(campaign_links)
        logger.info(f"Finally, got ({len(set_of_campaign_links)}) of campaign links.")
        return set_of_campaign_links

    def _find_campaign_links(self, publisher_link: str):
        campaign_links = []

        logger.info(f"Visiting {publisher_link} ...")

        try:
            if not self.web_browser_client.visit(publisher_link):
                logger.error(f"Failed to visit {publisher_link}")
                return []
            time_to_wait_in_sec = 1
            time.sleep(time_to_wait_in_sec)
            res = self.web_browser_client.get_page_source()
            soup = BeautifulSoup(res, "html.parser")
        except selenium.common.exceptions.WebDriverException as e:
            logger.error(f"Selenium WebDriverException while processing publisher link: {publisher_link}")
            logger.error(e)
            return []
        except Exception as e:
            logger.error(f"Unexpected exception while processing publisher link: {publisher_link}")
            logger.error(e)
            return []

        list_of_article_elements = soup.find_all("span", class_="list_subject")
        partial_article_links = []
        for span in list_of_article_elements:
            a_tag = span.find("a", href=True)
            if a_tag and "네이버" in a_tag.text:
                partial_article_links.append(a_tag["href"])

        for partial_article_link in partial_article_links:
            article_link = urljoin(publisher_link, partial_article_link)

            cached_links = self.article_link_to_campaign_link_cache.get(article_link)
            if cached_links is not None:
                logger.info(f"Cache hit. Using cached entries. ({article_link})")
                campaign_links.extend(cached_links)
                continue

            article_campaign_links = self._get_campaign_links_from_article(article_link)

            self.article_link_to_campaign_link_cache.put(article_link, article_campaign_links)
            campaign_links.extend(article_campaign_links)

        logger.info(f"Got ({len(campaign_links)}) of campaign links.")
        return campaign_links

    def _get_campaign_links_from_article(self, article_link: str) -> List[str]:

        article_campaign_links = []
        inner_soup = None

        logger.info(f"Visiting {article_link} ...")
        try:
            if not self.web_browser_client.visit(article_link):
                logger.error(f"Failed to visit {article_link}")
                return []
            time_to_wait_in_sec = 1
            time.sleep(time_to_wait_in_sec)
            res = self.web_browser_client.get_page_source()
            inner_soup = BeautifulSoup(res, "html.parser")
        except selenium.common.exceptions.WebDriverException as e:
            logger.error(f"Selenium WebDriverException while processing article link: {article_link}")
            logger.error(e)
            return []
        except Exception as e:
            logger.error(f"Unexpected exception while processing article link: {article_link}")
            logger.error(e)
            return []

        for a_tag in inner_soup.find_all("a", href=True):
            campaign_link = a_tag["href"]
            if self.is_starting_with_campaign_url(campaign_link):
                article_campaign_links.append(campaign_link)
            else:
                # Debugging info.
                # Only log when it looks like a URL but not a campaign link.
                const_site_inner_link_substring = "clien"
                if campaign_link.find("http") != -1 and campaign_link.find(const_site_inner_link_substring) == -1:
                    logger.info(f"Not a campaign link: {campaign_link}")

        return article_campaign_links
