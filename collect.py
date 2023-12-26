import pprint
import re
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
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def main():
    user_config = read_user_config()
    if not user_config:
        print("The config file is not valid.")
        exit(-1)
    
    visit_with_user_config(user_config)


def read_user_config():
    config_file_name = "main_config.yaml"
    try:
        f = open(config_file_name, "r", encoding="utf-8")
        user_config = yaml.load(f.read(), Loader=Loader)
    except IOError:
        print("Could not read file:", config_file_name)        
        return dict()
    return user_config
  
# It assumes that `user_config` is valid. It does not check validity of `user_config`.
def visit_with_user_config(user_config):
    users = user_config["users"]
    for user in users:
      create_naver_session_and_visit(user["id"], user["pw"])


# It creates a naver session and visit campaign links.
# 적립 확인 링크 - https://new-m.pay.naver.com/pointshistory/list?category=all
def create_naver_session_and_visit(id, pw):
    print("[INFO] Creating a naver session and visit pages with ID:", id, flush=True)
    s = naver_session(id, pw)
    campaign_links = find_naver_campaign_links(base_url, key_for_visited_urls_file_path=id)
    if(campaign_links == []):
        print("All campaign links were visited.")
        return
    for link in campaign_links:
        response = s.get(link)
        print(response.text) # for debugging
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
    encData = '{"a":"%s-4","b":"1.3.4","d":[{"i":"id","b":{"a":["0,%s"]},"d":"%s","e":false,"f":false},{"i":"%s","e":true,"f":false}],"h":"1f","i":{"a":"Mozilla/5.0"}}' % (
        bvsd_uuid, nid, nid, npw)
    bvsd = '{"uuid":"%s","encData":"%s"}' % (bvsd_uuid, lzstring.LZString.compressToEncodedURIComponent(encData))

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


def get_full_visited_urls_file_path(key_for_visited_urls_file_path):
    full_visited_urls_file_path=('visited_urls.%s.txt') % (key_for_visited_urls_file_path)
    return full_visited_urls_file_path


def read_visited_urls_from_file(file_path):
    # Read visited URLs from file
    try:
        with open(file_path, 'r') as file:
            visited_urls = set(file.read().splitlines())
    except FileNotFoundError:
        visited_urls = set()
    return visited_urls


def write_visited_urls_to_file(file_path, visited_urls):
    # Save the updated visited URLs to the file
    with open(file_path, 'w') as file:
        for url in visited_urls:
            file.write(url + '\n')


def find_naver_campaign_links(base_url, key_for_visited_urls_file_path='default'):
    full_visited_urls_file_path = get_full_visited_urls_file_path(key_for_visited_urls_file_path)
    visited_urls = read_visited_urls_from_file(full_visited_urls_file_path)

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
        if full_link in visited_urls:
            continue  # Skip already visited links

        res = requests.get(full_link)
        inner_soup = BeautifulSoup(res.text, 'html.parser')

        # Find all links that start with the campaign URL
        for a_tag in inner_soup.find_all('a', href=True):
            if a_tag['href'].startswith("https://campaign2-api.naver.com"):
                campaign_links.append(a_tag['href'])

        # Add the visited link to the set
        visited_urls.add(full_link)
        write_visited_urls_to_file(full_visited_urls_file_path, visited_urls) 

    return campaign_links

# The base URL to start with
base_url = "https://www.clien.net/service/board/jirum"
#base_url = "https://www.clien.net/service/board/park"


if __name__ == "__main__":
    main()
