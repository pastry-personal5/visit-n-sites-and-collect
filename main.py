"""
This module visits Naver Pay's advertisement sites or campaign links.
And it collects a small amount of money.
The source code is derived from an article in https://www.clien.net.
The original author is unknown.
Please visit and find the original author. i.e. https://www.clien.net/service/board/kin/18490638
Please look for `LICENSE` file for license.
Please beware of file encoding.
"""
import datetime
import sys
import time
from urllib.parse import urljoin

from loguru import logger
import requests
import selenium
from selenium import common as SC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from bs4 import BeautifulSoup

import meta_info_manager
import publisher


class LinkVisitorClientContext:

    def __init__(self):
        self.driver = None # It's a Selenium driver.

    def clean_up(self):
        if self.driver:
            self.driver.quit()


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

class LinkFinderBase:

    def __init__(self, article_link_to_campaign_link_cache: ArticleLinkToCampaignLinkCache):
        self.article_link_to_campaign_link_cache = article_link_to_campaign_link_cache  # It's a shared object. Let's reference it.

class LinkFinderForC1WebSite(LinkFinderBase):

    def find_set_of_campaign_links(self, days_difference_since_last_run: int) -> set[str]:
        set_of_campaign_links = set()
        publisher_links_to_visit = publisher.create_publisher_links_to_visit(days_difference_since_last_run)  # With help from |current_meta_info_manager|
        for publisher_link in publisher_links_to_visit:
            campaign_links = self.find_campaign_links(publisher_link)
            set_of_campaign_links.update(campaign_links)
        logger.info(f'In this method, got ({len(set_of_campaign_links)}) of campaign links.')
        return set_of_campaign_links

    def find_campaign_links(self, publisher_link: str):
        logger.info(f'Visiting ({publisher_link})...')
        # Send a request to the |publisher_link|
        try:
            response = requests.get(publisher_link)
        except requests.exceptions.ConnectionError:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all span elements with class 'list_subject' and get 'a' tags
        list_subject_links = soup.find_all('span', class_='list_subject')
        partial_article_links = []
        for span in list_subject_links:
            a_tag = span.find('a', href=True)
            if a_tag and '네이버' in a_tag.text:
                partial_article_links.append(a_tag['href'])

        # Initialize a list to store campaign links
        campaign_links = []

        # Check each Naver link
        for partial_article_link in partial_article_links:
            article_link = urljoin(publisher_link, partial_article_link)

            # It looks up an entry in the cache, first.
            campaign_links = self.article_link_to_campaign_link_cache.get(article_link)
            if campaign_links:
                logger.info(f'Cache hit. Now returning entries from the cache. ({article_link})')
                return campaign_links

            logger.info(f'Visiting ({article_link})...')
            campaign_links = []
            try:
                res = requests.get(article_link)
            except requests.exceptions.ConnectionError:
                logger.warning(f'Could not get the link: ({article_link}). Continue...')
                continue
            inner_soup = BeautifulSoup(res.text, 'html.parser')

            # Find all links that start with the campaign URL
            for a_tag in inner_soup.find_all('a', href=True):
                if a_tag['href'].startswith('https://campaign2-api.naver.com/'):
                    campaign_links.append(a_tag['href'])

            # Note: The length of |campaign_links| can be zero. It's intentional.
            self.article_link_to_campaign_link_cache.put(article_link, campaign_links)

        logger.info(f'Got ({len(campaign_links)}) of campaign links.')

        return campaign_links


class LinkFinderForD1WebSite(LinkFinderBase):

    def find_set_of_campaign_links(self, days_difference_since_last_run: int):
        return None

class LinkFinderCreator:

    const_c1 = 0
    const_d1 = 1

    def __init__(self):
        pass

    def build_link_finder(self, visitor_type: int, article_link_to_campaign_link_cache: ArticleLinkToCampaignLinkCache):
        if visitor_type == self.const_c1:
            return LinkFinderForC1WebSite(article_link_to_campaign_link_cache)
        if visitor_type == self.const_d1:
            return LinkFinderForD1WebSite(article_link_to_campaign_link_cache)
        else:
            return None


class MainController:

    def __init__(self):
        self.article_link_to_campaign_link_cache = ArticleLinkToCampaignLinkCache()

    def find_and_visit_all(self, user_config: dict):
        # This method is a main entry point.
        users = user_config["users"]
        for user in users:
            nid = user['id']
            npw = user['pw']
            set_of_campaign_links = self.find_all(nid)
            self.visit_all(nid, npw, set_of_campaign_links)

    def find_all(self, nid) -> set[str]:
        days_difference_since_last_run = self.get_days_difference_since_last_run(nid)
        link_finders = []

        # Now one has just two link finder objects. Therefore, |link_finders| is going to get two elements.
        link_finder_creator = LinkFinderCreator()
        c1_link_finder = link_finder_creator.build_link_finder(LinkFinderCreator.const_c1, self.article_link_to_campaign_link_cache)
        d1_link_finder = link_finder_creator.build_link_finder(LinkFinderCreator.const_d1, self.article_link_to_campaign_link_cache)
        link_finders.append(c1_link_finder)
        link_finders.append(d1_link_finder)

        # Union all using |update| method of |set|
        set_of_campaign_links = set()
        for link_finder in link_finders:
            # Look for |LinkFinderForC1WebSite.find_set_of_campaign_links| as an example...
            result = link_finder.find_set_of_campaign_links(days_difference_since_last_run)
            if result:
                set_of_campaign_links.update(result)
        return set_of_campaign_links

    def visit_all(self, nid, npw, set_of_campaign_links: set[str]) -> None:
        # It creates a Naver session and visit campaign links.
        # 적립 확인 링크 - https://new-m.pay.naver.com/pointshistory/list?category=all
        logger.info(f'Creating a Naver session and visit pages with ID: ({nid}), if needed.')
        client_context = None
        current_meta_info_manager = meta_info_manager.MetaInfoManager(nid)
        prepare_visit(current_meta_info_manager)
        self.visit(set_of_campaign_links, client_context, current_meta_info_manager, nid, npw)
        finish_visit(current_meta_info_manager)
        if client_context:
            client_context.clean_up()


    def visit(self, set_of_campaign_links, client_context, current_meta_info_manager: meta_info_manager.MetaInfoManager, nid, npw):
        for campaign_link in set_of_campaign_links:
            if current_meta_info_manager.is_visited_campaign_link(campaign_link):
                continue
            try:
                logger.info(f'Visiting a campaign link: {campaign_link}')
                client_context = lazy_init_client_context_if_needed(client_context, nid, npw)
                if not client_context:
                    return
                client_context.driver.get(campaign_link)
                if EC.alert_is_present():
                    try:
                        client_context.driver.switch_to.alert.accept()
                    except SC.exceptions.NoAlertPresentException:
                        pass
                record_visit(current_meta_info_manager, campaign_link)
            except SC.exceptions.UnexpectedAlertPresentException:
                pass

            const_time_to_sleep_in_sec = 5
            time.sleep(const_time_to_sleep_in_sec)

    def get_days_difference_since_last_run(self, nid) -> int:
        current_meta_info_manager = meta_info_manager.MetaInfoManager(nid)
        date_of_last_run = current_meta_info_manager.read_date_of_last_run()
        if date_of_last_run != -1:
            today = datetime.date.today()
            days = (today - date_of_last_run).days
            return days
        return -1


def main():
    main_controller = MainController()
    user_config = read_user_config()
    if not user_config:
        logger.error("The config file is not valid.")
        sys.exit(-1)

    main_controller.find_and_visit_all(user_config)


def read_user_config():
    config_file_name = "main_config.yaml"
    try:
        f = open(config_file_name, "r", encoding="utf-8")
        user_config = yaml.load(f.read(), Loader=Loader)
    except IOError:
        logger.error('Could not read file: {config_file_name}')
        return {}
    return user_config


def prepare_visit(current_meta_info_manager: meta_info_manager.MetaInfoManager):
    current_meta_info_manager.read_visited_campaign_links_from_file()


def finish_visit(current_meta_info_manager: meta_info_manager.MetaInfoManager):
    current_meta_info_manager.write_visited_campaign_links_to_file()
    current_meta_info_manager.write_date_of_last_run()


def record_visit(current_meta_info_manager: meta_info_manager.MetaInfoManager, campaign_link):
    current_meta_info_manager.record_visited_campaign_link(campaign_link)

def create_link_visitor_client_context_with_selenium(nid, npw):
    driver = webdriver.Chrome()
    driver.implicitly_wait(0.5)

    client_context = LinkVisitorClientContext()
    client_context.driver = driver

    visit_login_page(driver, nid, npw)

    return client_context


def wait_for_page_load(driver):
    while True:
        try:
            title = driver.title
            if title == '네이버페이':
                break
        except selenium.common.exceptions.NoSuchWindowException:
            logger.info('A user has closed the Chrome window.')
            sys.exit(-1)

        try:
            element_not_to_register_device = driver.find_element(by=By.ID, value="new.dontsave")
            if element_not_to_register_device:
                break
        except selenium.common.exceptions.NoSuchElementException:
            pass
        const_time_to_sleep_in_sec = 1
        time.sleep(const_time_to_sleep_in_sec)


def visit_login_page(driver, nid, npw):
    driver.get("https://new-m.pay.naver.com/pcpay?page=1")
    const_time_to_wait = 16
    WebDriverWait(driver, const_time_to_wait).until(
        EC.presence_of_element_located((By.ID, 'id'))
    )

    element_for_id = driver.find_element(by=By.ID, value="id")
    element_for_password = driver.find_element(by=By.ID, value="pw")
    element_for_submission = driver.find_element(by=By.ID, value="submit_btn")  # Previously, the HTML element ID was log.login

    element_for_id.send_keys(nid)
    element_for_password.send_keys(npw)

    element_for_submission.click()

    wait_for_page_load(driver)

    try:
        element_not_to_register_device = driver.find_element(by=By.ID, value="new.dontsave")
        if element_not_to_register_device:
            element_not_to_register_device.click()
            wait_for_page_load(driver)
    except SC.exceptions.NoSuchElementException:
        pass


def create_link_visitor_client_context(nid, npw):
    return create_link_visitor_client_context_with_selenium(nid, npw)


def lazy_init_client_context_if_needed(client_context, nid, npw):
    if client_context:
        return client_context
    client_context = create_link_visitor_client_context(nid, npw)
    if not client_context:
        logger.error(f'Could not sign in with an ID: {nid}')
        return None
    return client_context


if __name__ == "__main__":
    main()
