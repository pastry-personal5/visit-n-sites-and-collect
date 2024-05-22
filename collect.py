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

import requests
from selenium import common as SC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from bs4 import BeautifulSoup

import publisher


# `LinkRecorder` records visited links or URLs.
# Visited links belong to nid or Naver user ID.
class LinkRecorder:
    visited_links = set()
    nid = None

    # nid means Naver user ID.
    def __init__(self, nid: str):
        self.nid = nid

    def is_visited(self, url: str):
        return url in self.visited_links

    def add_link(self, url: str):
        self.visited_links.add(url)

    def get_visited_urls(self):
        return self.visited_links

    def get_full_visited_urls_file_path(self):
        full_visited_urls_file_path = f'visited_urls.{self.nid}.txt'
        return full_visited_urls_file_path

    def read_visited_urls_from_file(self):
        file_path = self.get_full_visited_urls_file_path()
        # Read visited URLs from file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.visited_links = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_links = set()
        return self.visited_links

    def write_visited_urls_to_file(self):
        # Save the updated visited URLs to the file
        file_path = self.get_full_visited_urls_file_path()
        with open(file_path, 'w', encoding='utf-8') as file:
            for url in self.visited_links:
                file.write(url + '\n')


class LinkVisitorClientContext:
    driver = None  # It's a Selenium driver.

    def __init__(self):
        self.driver = None

    def clean_up(self):
        if self.driver:
            self.driver.quit()


def main():
    user_config = read_user_config()
    if not user_config:
        print("The config file is not valid.")
        sys.exit(-1)

    visit_with_user_config(user_config)


def read_user_config():
    config_file_name = "main_config.yaml"
    try:
        f = open(config_file_name, "r", encoding="utf-8")
        user_config = yaml.load(f.read(), Loader=Loader)
    except IOError:
        print("[ERROR] Could not read file:", config_file_name)
        return {}
    return user_config


# It assumes that `user_config` is valid. It does not check validity of `user_config`.
def visit_with_user_config(user_config):
    users = user_config["users"]
    for user in users:
        create_naver_session_and_visit(user["id"], user["pw"])


def prepare_visit(link_recorder):
    link_recorder.read_visited_urls_from_file()


def finish_visit(link_recorder, nid):
    link_recorder.write_visited_urls_to_file()
    publisher.record_successful_visit(nid)


def create_link_visitor_client_context_with_selenium(nid, npw):
    driver = webdriver.Chrome()
    driver.implicitly_wait(0.5)

    client_context = LinkVisitorClientContext()
    client_context.driver = driver

    visit_login_page(driver, nid, npw)

    return client_context


def get_continue_command_from_user():
    while True:
        ch = input('Please input \'c\' to continue...')
        if ch == 'c':
            return


def visit_login_page(driver, nid, npw):
    driver.get("https://new-m.pay.naver.com/pcpay?page=1")
    title = driver.title
    print(f'title (%s)' % title)

    element_for_id = driver.find_element(by=By.ID, value="id")
    element_for_password = driver.find_element(by=By.ID, value="pw")
    element_for_submission = driver.find_element(by=By.ID, value="log.login")

    element_for_id.send_keys(nid)
    element_for_password.send_keys(npw)

    element_for_submission.click()

    get_continue_command_from_user()
    title = driver.title
    print(f'title (%s)' % title)

    try:
        element_for_registering_device = driver.find_element(by=By.ID, value="new.save")
        if element_for_registering_device:
            element_for_registering_device.click()
            get_continue_command_from_user()
            title = driver.title
            print(f'title (%s)' % title)
    except SC.exceptions.NoSuchElementException:
        pass


def create_link_visitor_client_context(nid, npw):
    client_context = create_link_visitor_client_context_with_selenium(nid, npw)
    return client_context


# It creates a Naver session and visit campaign links.
# 적립 확인 링크 - https://new-m.pay.naver.com/pointshistory/list?category=all
def create_naver_session_and_visit(nid, npw):
    print("[INFO] Creating a naver session and visit pages with ID:", nid, flush=True)
    client_context = create_link_visitor_client_context(nid, npw)
    if not client_context:
        print("[ERROR] Could not sign in with an ID: ", nid)
        return
    link_recorder = LinkRecorder(nid)
    publisher_urls_to_visit = publisher.create_publisher_urls_to_visit(nid)
    prepare_visit(link_recorder)
    visit(publisher_urls_to_visit, client_context, link_recorder)
    finish_visit(link_recorder, nid)
    client_context.clean_up()


def visit(base_urls, link_visitor_context, link_recorder):
    TIME_TO_SLEEP = 5
    for base_url in base_urls:
        print("[INFO] Visiting:", base_url, flush=True)
        campaign_urls = find_naver_campaign_urls(link_recorder, base_url)
        if not campaign_urls:
            print("[INFO] All campaign links were visited.")
            continue
        for link in campaign_urls:
            try:
                print("[INFO] Visiting a campaign link: ", link, flush=True)
                link_visitor_context.driver.get(link)
                if EC.alert_is_present():
                    try:
                        link_visitor_context.driver.switch_to.alert.accept()
                    except SC.exceptions.NoAlertPresentException:
                        pass
            except SC.exceptions.UnexpectedAlertPresentException:
                pass

            time.sleep(TIME_TO_SLEEP)


def find_naver_campaign_urls(link_recorder, base_url):
    # Send a request to the base URL
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all span elements with class 'list_subject' and get 'a' tags
    list_subject_links = soup.find_all('span', class_='list_subject')
    naver_links = []
    for span in list_subject_links:
        a_tag = span.find('a', href=True)
        if a_tag and '네이버' in a_tag.text:
            naver_links.append(a_tag['href'])

    # Initialize a list to store campaign links
    campaign_urls = []

    # Check each Naver link
    for link in naver_links:
        full_link = urljoin(base_url, link)
        if link_recorder.is_visited(full_link):
            continue  # Skip already visited links

        res = requests.get(full_link)
        inner_soup = BeautifulSoup(res.text, 'html.parser')

        # Find all links that start with the campaign URL
        for a_tag in inner_soup.find_all('a', href=True):
            if a_tag['href'].startswith("https://campaign2-api.naver.com"):
                campaign_urls.append(a_tag['href'])

        # Add the visited link to the set
        link_recorder.add_link(full_link)

    return campaign_urls


if __name__ == "__main__":
    main()
