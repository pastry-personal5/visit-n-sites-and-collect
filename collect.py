"""
This module visits Naver Pay's advertisement sites or campaign links.
And it collects a small amount of money.
The source code is derived from an article in https://www.clien.net.
The original author is unknown.
Please visit and find the original author. i.e. https://www.clien.net/service/board/kin/18490638
Please look for `LICENSE` file for license.
Please beaware of file encoding.
"""
import re
import sys
import time
from urllib.parse import urljoin
import uuid

import requests
import rsa
import lzstring
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup

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
        print("Could not read file:", config_file_name)
        return {}
    return user_config


# It assumes that `user_config` is valid. It does not check validity of `user_config`.
def visit_with_user_config(user_config):
    users = user_config["users"]
    for user in users:
        create_naver_session_and_visit(user["id"], user["pw"])


def prepare_visit(link_recorder):
    link_recorder.read_visited_urls_from_file()


def finish_visit(link_recorder):
    link_recorder.write_visited_urls_to_file()


# It creates a Naver session and visit campaign links.
# 적립 확인 링크 - https://new-m.pay.naver.com/pointshistory/list?category=all
def create_naver_session_and_visit(nid, npw):
    print("[INFO] Creating a naver session and visit pages with ID:", nid, flush=True)
    s = naver_session(nid, npw)
    link_recorder = LinkRecorder(nid)
    prepare_visit(link_recorder)
    visit(s, link_recorder)
    finish_visit(link_recorder)


def visit(session, link_recorder):
    TARGET_BASE_URL_LIST = [
        # The base URL to start with
        "https://www.clien.net/service/board/jirum",
        "https://www.clien.net/service/board/park"
    ]
    for base_url in TARGET_BASE_URL_LIST:
        print("[INFO] Visiting:", base_url, flush=True)
        campaign_links = find_naver_campaign_links(link_recorder, base_url)
        if not campaign_links:
            print("[INFO] All campaign links were visited.")
            continue
        for link in campaign_links:
            response = session.get(link)
            print(response.text)  # for debugging
            response.raise_for_status()
            time.sleep(5)
            print("Campaign URL : " + link)


def encrypt(key_str, uid, upw):
    def naver_style_join(l):
        return ''.join([chr(len(s)) + s for s in l])

    sessionkey, keyname, e_str, n_str = key_str.split(',')
    e, n = int(e_str, 16), int(n_str, 16)

    message = naver_style_join([sessionkey, uid, upw]).encode()

    pubkey = rsa.PublicKey(e, n)
    encrypted = rsa.encrypt(message, pubkey)

    return keyname, encrypted.hex()


def encrypt_account(uid, upw):
    key_str = requests.get('https://nid.naver.com/login/ext/keys.nhn').content.decode("utf-8")
    return encrypt(key_str, uid, upw)


def naver_session(nid, npw):
    encnm, encpw = encrypt_account(nid, npw)

    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
    s.mount('https://', HTTPAdapter(max_retries=retries))
    request_headers = {
        'User-agent': 'Mozilla/5.0'
    }

    bvsd_uuid = uuid.uuid4()
    enc_data = '{"a":"%s-4","b":"1.3.4","d":[{"i":"id","b":{"a":["0,%s"]},"d":"%s","e":false,"f":false},{"i":"%s","e":true,"f":false}],"h":"1f","i":{"a":"Mozilla/5.0"}}' % (
        bvsd_uuid, nid, nid, npw)
    bvsd = '{"uuid":"%s","encData":"%s"}' % (bvsd_uuid, lzstring.LZString.compressToEncodedURIComponent(enc_data))

    resp = s.post('https://nid.naver.com/nidlogin.login', data={
        'svctype': '0',
        'enctp': '1',
        'encnm': encnm,
        'enc_url': 'http0X0.0000000000001P-10220.0000000.000000www.naver.com',
        'url': 'www.naver.com',
        'smart_level': '1',
        'encpw': encpw,
        'bvsd': bvsd
        }, headers=request_headers)

    print(resp.content)

    finalize_url = re.search(r'location\.replace\("([^"]+)"\)', resp.content.decode("utf-8")).group(1)
    s.get(finalize_url)

    return s


def find_naver_campaign_links(link_recorder, base_url):
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
    campaign_links = []

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
                campaign_links.append(a_tag['href'])

        # Add the visited link to the set
        link_recorder.add_link(full_link)

    return campaign_links


if __name__ == "__main__":
    main()
