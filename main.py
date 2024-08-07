"""
This module visits Naver Pay's advertisement sites or campaign links.
And it collects a small amount of money.
The source code is derived from an article in https://www.clien.net.
The original author is unknown.
Please visit and find the original author. i.e. https://www.clien.net/service/board/kin/18490638
Please look for `LICENSE` file for license.
Please beware of file encoding.
"""
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


def main():
    user_config = read_user_config()
    if not user_config:
        logger.error("The config file is not valid.")
        sys.exit(-1)

    visit_with_user_config(user_config)


def read_user_config():
    config_file_name = "main_config.yaml"
    try:
        f = open(config_file_name, "r", encoding="utf-8")
        user_config = yaml.load(f.read(), Loader=Loader)
    except IOError:
        logger.error('Could not read file: {config_file_name}')
        return {}
    return user_config


# It assumes that `user_config` is valid. It does not check validity of `user_config`.
def visit_with_user_config(user_config):
    users = user_config["users"]
    for user in users:
        create_naver_session_and_visit(user["id"], user["pw"])


def prepare_visit(current_meta_info_manager: meta_info_manager.MetaInfoManager):
    current_meta_info_manager.read_visited_campaign_links_from_file()


def finish_visit(current_meta_info_manager: meta_info_manager.MetaInfoManager):
    current_meta_info_manager.write_visited_campaign_links_to_file()
    current_meta_info_manager.write_date_of_last_run()


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


# It creates a Naver session and visit campaign links.
# 적립 확인 링크 - https://new-m.pay.naver.com/pointshistory/list?category=all
def create_naver_session_and_visit(nid, npw):
    logger.info(f'Creating a Naver session and visit pages with ID: {nid}')
    client_context = None
    current_meta_info_manager = meta_info_manager.MetaInfoManager(nid)
    publisher_links_to_visit = publisher.create_publisher_links_to_visit(current_meta_info_manager)  # With help from |current_meta_info_manager|
    prepare_visit(current_meta_info_manager)
    visit(publisher_links_to_visit, client_context, current_meta_info_manager, nid, npw)
    finish_visit(current_meta_info_manager)
    if client_context:
        client_context.clean_up()


def visit(publisher_links_to_visit, client_context, current_meta_info_manager, nid, npw):

    for publisher_link in publisher_links_to_visit:
        logger.info(f'Visiting: {publisher_link}')
        campaign_links = find_naver_campaign_links(current_meta_info_manager, publisher_link)
        if not campaign_links:
            logger.info('All campaign links were visited.')
            continue
        for link in campaign_links:
            try:
                logger.info(f'Visiting a campaign link: {link}')
                client_context = lazy_init_client_context_if_needed(client_context, nid, npw)
                if not client_context:
                    return
                client_context.driver.get(link)
                if EC.alert_is_present():
                    try:
                        client_context.driver.switch_to.alert.accept()
                    except SC.exceptions.NoAlertPresentException:
                        pass
            except SC.exceptions.UnexpectedAlertPresentException:
                pass

            const_time_to_sleep_in_sec = 5
            time.sleep(const_time_to_sleep_in_sec)


def find_naver_campaign_links(current_meta_info_manager: meta_info_manager.MetaInfoManager, publisher_link):
    # Send a request to the |publisher_link|
    response = requests.get(publisher_link)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all span elements with class 'list_subject' and get 'a' tags
    list_subject_links = soup.find_all('span', class_='list_subject')
    naver_links = []
    for span in list_subject_links:
        a_tag = span.find('a', href=True)
        if a_tag and '네이버' in a_tag.text:
            naver_links.append(a_tag['href'])

    # Initialize a list to store campaign links
    campaign_links = []

    # Check each Naver link
    for link in naver_links:
        full_link = urljoin(publisher_link, link)
        if current_meta_info_manager.is_visited_campaign_link(full_link):
            continue  # Skip already visited links

        res = requests.get(full_link)
        inner_soup = BeautifulSoup(res.text, 'html.parser')

        # Find all links that start with the campaign URL
        for a_tag in inner_soup.find_all('a', href=True):
            if a_tag['href'].startswith('https://campaign2-api.naver.com/'):
                campaign_links.append(a_tag['href'])

        # Add the visited link to the set
        current_meta_info_manager.record_visited_campaign_link(full_link)

    return campaign_links


if __name__ == "__main__":
    main()
