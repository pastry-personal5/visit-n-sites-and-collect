import time

from bs4 import BeautifulSoup
from loguru import logger
import selenium
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

import undetected_chromedriver as UC

from src.visit_n_sites_and_collect.link_finder_impl_base import LinkFinderImplBase
from src.visit_n_sites_and_collect.publisher import PublisherController
from src.visit_n_sites_and_collect.article_link_to_campaign_link_cache import ArticleLinkToCampaignLinkCache


class WebBrowserClient():
    def __init__(self):
        self.driver = None

    def prepare(self) -> None:
        try:
            self.driver = UC.Chrome()
            self.driver.implicitly_wait(0.5)
        except WebDriverException as e:
            logger.error("Failed to initialize Chrome WebDriver.")
            logger.error(e)
            self.driver = None

    def cleanup(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning("Exception during browser cleanup.")
                logger.warning(e)

    def visit(self, url: str) -> bool:
        if not self.driver:
            logger.error("WebDriver not initialized.")
            return False
        try:
            self.driver.get(url)
            return True
        except selenium.common.exceptions.WebDriverException as e:
            logger.error(f"Error visiting {url}")
            logger.error(e)
            return False

    def get_page_source(self) -> str:
        if not self.driver:
            logger.error("WebDriver not initialized.")
            return ""
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error("Error getting page source.")
            logger.error(e)
            return ""


class LinkFinderForD1WebSiteImpl(LinkFinderImplBase):

    def __init__(self, article_link_to_campaign_link_cache: ArticleLinkToCampaignLinkCache):
        super().__init__(article_link_to_campaign_link_cache)
        self.web_browser_client = WebBrowserClient()
        self.web_browser_client.prepare()

    def cleanup(self) -> None:
        self.web_browser_client.cleanup()

    def get_publisher_meta(self) -> tuple[str, str]:
        target_base_url_list = [
            # The base URL to start with
            "https://damoang.net/economy"
        ]

        template_list = ["https://damoang.net/economy?page=%d"]
        return (target_base_url_list, template_list)

    def find_set_of_campaign_links(self, days_difference_since_last_run: int) -> set[str]:
        """
        The function `find_set_of_campaign_links` retrieves a set of campaign links from a list of
        publisher links based on a specified number of days since the last run.

        :param days_difference_since_last_run: The parameter `days_difference_since_last_run` is an
        integer that represents the number of days since the last run of the function. This parameter is
        used to determine which campaign links to retrieve based on the specified time difference
        :type days_difference_since_last_run: int
        :return: The function `find_set_of_campaign_links` returns a set of strings, which contains
        campaign links.
        """
        (target_base_url_list, template_list) = self.get_publisher_meta()
        publisher_controller = PublisherController()
        publisher_links_to_visit = publisher_controller.create_publisher_links_to_visit(target_base_url_list, template_list, days_difference_since_last_run)
        set_of_campaign_links = set()

        for publisher_link in publisher_links_to_visit:
            campaign_links = self.find_list_of_campaign_links(publisher_link)
            set_of_campaign_links.update(campaign_links)
        logger.info(f"Finally, got ({len(set_of_campaign_links)}) of campaign links.")
        return set_of_campaign_links

    def find_list_of_campaign_links(self, publisher_link: str) -> list[str]:
        """
        The function `find_list_of_campaign_links` retrieves a list of campaign links from a given
        publisher link by extracting links from articles and then extracting campaign links from those
        articles.

        :param publisher_link: The `find_list_of_campaign_links` method takes a `publisher_link`
        parameter, which is a string representing the link to the publisher's website. This method aims
        to find a list of campaign links related to the articles found on the publisher's website. It
        achieves this by first obtaining a list of
        :type publisher_link: str
        :return: A list of campaign links is being returned.
        """
        list_to_return = []
        list_of_article_links = self.find_list_of_article_links(publisher_link)
        for article_link in list_of_article_links:
            list_of_campaign_links = self.find_list_of_campaign_links_in_article(article_link)
            list_to_return.extend(list_of_campaign_links)
        return list_to_return

    def find_list_of_campaign_links_in_article(self, article_link: str) -> list[str]:
        """
        This Python function finds and returns a list of campaign links from a given article link,
        utilizing caching for efficiency.

        :param article_link: The `article_link` parameter in the
        `find_list_of_campaign_links_in_article` method is a string that represents the link to an
        article. This method is designed to find a list of campaign links within the content of the
        article specified by the `article_link`
        :type article_link: str
        :return: a list of campaign links found in the article referenced by the input `article_link`.
        """

        logger.info(f"The reference link of an article is: {article_link}")

        # It looks up an entry in the cache, first.
        list_of_campaign_links = self.article_link_to_campaign_link_cache.get(article_link)
        if list_of_campaign_links:
            # Cache hit.
            logger.info(f"Cache hit. Now returning entries from the cache: {article_link}")
            return list_of_campaign_links

        # Cache miss.
        list_of_campaign_links = []

        logger.info(f"Visiting: {article_link} ...")
        try:
            if not self.web_browser_client.visit(article_link):
                logger.error(f"Failed to visit {article_link}")
                return []
            time_to_wait_in_sec = 0.2
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

        # Find all links that start with the campaign URL
        for a_tag in inner_soup.find_all("a", href=True):
            campaign_link = a_tag["href"]
            if self.is_starting_with_campaign_url(campaign_link):
                list_of_campaign_links.append(campaign_link)
            else:
                # Log only significant links.
                # We don't want to log all links, because there are too many of them.
                if campaign_link.find("http") != -1 and campaign_link.find("damoang") == -1:
                    logger.info(f"Not a campaign link: {campaign_link}")
        logger.info(f"Got ({len(list_of_campaign_links)}) of campaign links.")

        # Note: The length of |list_of_campaign_links| can be zero. It's intentional.
        self.article_link_to_campaign_link_cache.put(article_link, list_of_campaign_links)
        return list_of_campaign_links

    def find_list_of_article_links(self, publisher_link: str) -> list[str]:
        """
        The function `find_list_of_article_links` retrieves a list of article links from a given
        publisher link by parsing the HTML content.

        :param publisher_link: The `publisher_link` parameter in the `find_list_of_article_links`
        function is a string that represents the URL of a publisher's website. This function sends a
        request to the provided `publisher_link`, extracts the article links from the HTML content of
        the page, and returns a list of article links
        :type publisher_link: str
        :return: The function `find_list_of_article_links` returns a list of article links that are
        found within the `<li>` elements with class 'list-group-item' on the webpage specified by the
        `publisher_link`. The links are filtered based on the condition that the anchor text of the link
        contains the word '네이버' (which means 'Naver' in Korean).
        """
        # Send a request to the |publisher_link|
        logger.info(f"Visiting: {publisher_link} ...")

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

        # Find all <li> elements with class 'list-group-item' and get <a> elements
        list_of_article_elements = soup.find_all("li", class_="list-group-item")
        list_of_article_links = []
        for article_element in list_of_article_elements:
            a_tags = article_element.find_all("a", href=True)
            if a_tags:
                for a_tag in a_tags:
                    if a_tag and "네이버" in a_tag.text and a_tag.has_attr("class") and ("da-article-link" in a_tag.get("class", [])):
                        article_link = a_tag["href"]
                        if article_link.startswith("/promotion"):
                            article_link = "https://damoang.net" + article_link
                        list_of_article_links.append(article_link)
                        logger.info(f"article_link: {article_link}")

        return list_of_article_links
