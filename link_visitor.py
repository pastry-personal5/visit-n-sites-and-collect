import sys
import time

from loguru import logger
import selenium
from selenium import common as SC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from meta_info_manager import SharedContext
import meta_info_manager


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


class LinkVisitorClientContext:

    def __init__(self):
        self.driver = None  # It's a Selenium driver.

    def clean_up(self):
        if self.driver:
            self.driver.quit()


class LinkVisitor:

    def __init__(self):
        pass

    def visit_all(self, nid, npw, set_of_campaign_links: set[str], shared_context: SharedContext) -> None:
        # It creates a Naver session and visit campaign links.
        # 적립 확인 링크 - https://new-m.pay.naver.com/pointshistory/list?category=all
        logger.info(f'Creating a Naver session and visit pages with ID: ({nid}), if needed.')
        client_context = None
        current_meta_info_manager = meta_info_manager.MetaInfoManager(nid, shared_context)
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
                driver = client_context.driver
                driver.get(campaign_link)

                if EC.alert_is_present():
                    try:
                        driver.switch_to.alert.accept()
                    except SC.exceptions.NoAlertPresentException:
                        pass

                if campaign_link.startswith('https://campaign2.naver.com/'):
                    const_time_to_wait_in_sec = 16
                    WebDriverWait(driver, const_time_to_wait_in_sec).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'popup_link'))
                    )
                    element_to_go_to_the_next_step = driver.find_element(By.CLASS_NAME, 'popup_link')
                    if element_to_go_to_the_next_step:
                        try:
                            element_to_go_to_the_next_step.click()
                        except SC.ElementNotInteractableException:
                            pass

                record_visit(current_meta_info_manager, campaign_link)
            except SC.exceptions.UnexpectedAlertPresentException:
                pass

            const_time_to_sleep_in_sec = 5
            time.sleep(const_time_to_sleep_in_sec)
