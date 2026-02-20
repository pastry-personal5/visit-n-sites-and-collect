from abc import abstractmethod
import os
import sys
import time

import gzip
from loguru import logger
import selenium
import selenium.common as SC
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import shutil
import undetected_chromedriver as UC

from src.visit_n_sites_and_collect.cloud_file_storage import CloudFileStorage
from src.visit_n_sites_and_collect.configuration_for_cloud_file_storage import ConfigurationForCloudFileStorage
from src.visit_n_sites_and_collect.last_run_recorder import LastRunRecorder
from src.visit_n_sites_and_collect.global_config import GlobalConfigIR
from src.visit_n_sites_and_collect.constants import Constants


class VisitedCampaignLinkControllerBase:

    @abstractmethod
    def set_unique_id(self, unique_id: str) -> None:
        pass

    @abstractmethod
    def prepare_visit(self) -> None:
        pass

    @abstractmethod
    def finish_visit(self) -> None:
        pass

    @abstractmethod
    def is_visited_campaign_link(self, campaign_link: str) -> bool:
        pass

    @abstractmethod
    def record_visit(self, campaign_link: str) -> None:
        pass

    @abstractmethod
    def delete_all(self) -> None:
        pass


class VisitedCampaignLinkController(VisitedCampaignLinkControllerBase):
    """
    A class that records visited campaign links.
    """

    def __init__(self):
        self.nid = None
        self.visited_links = None
        self.configuration_for_cloud_file_storage = None  # This can be None. This is a configuration for cloud file storage.
        self.cloud_file_storage = None
        self.flag_use_cloud_file_storage = False

    def init_with_cloud_file_storage(self, configuration_for_cloud_file_storage: ConfigurationForCloudFileStorage, cloud_file_storage: CloudFileStorage) -> None:
        self.configuration_for_cloud_file_storage = configuration_for_cloud_file_storage
        self.cloud_file_storage = cloud_file_storage

    def reset_with_nid(self, nid: str) -> None:
        logger.info(f"Resetting with a new n-site ID: ({nid})")
        self.nid = nid
        self.visited_links = set()

    def prepare_visit(self) -> None:
        assert self.nid is not None
        self._read_visited_campaign_links_from_file()

    def finish_visit(self):
        assert self.nid is not None
        self._write_visited_campaign_links_to_file()

    def is_visited_campaign_link(self, campaign_link: str) -> bool:
        return campaign_link in self.visited_links

    def record_visit(self, campaign_link: str) -> None:
        self.visited_links.add(campaign_link)

    def get_visited_urls(self):
        return self.visited_links

    def _get_full_visited_urls_file_path(self):
        assert self.nid is not None
        full_visited_urls_file_name = f"visited_urls.{self.nid}.txt"
        file_path = os.path.join(Constants.data_dir_path, full_visited_urls_file_name)
        return file_path

    def _get_gzipped_full_visited_urls_file_path(self):
        assert self.nid is not None
        gzipped_full_visited_urls_file_name = f"visited_urls.{self.nid}.txt.gz"
        file_path = os.path.join(Constants.data_dir_path, gzipped_full_visited_urls_file_name)
        return file_path

    def _compress_file(self, input_file, output_file):
        with open(input_file, "rb") as f_in:
            with gzip.open(output_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    def _decompress_file(self, input_file, output_file):
        with gzip.open(input_file, "rb") as f_in:
            with open(output_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    def _read_visited_campaign_links_from_file(self):
        # Prepare
        gzipped_file_path = self._get_gzipped_full_visited_urls_file_path()
        file_path = self._get_full_visited_urls_file_path()
        basename_of_gzipped_file = os.path.basename(gzipped_file_path)

        if self.flag_use_cloud_file_storage:

            # Download a file from the cloud if available.
            if self.configuration_for_cloud_file_storage and self.configuration_for_cloud_file_storage.has_valid_cloud_file_storage_config():
                self.cloud_file_storage.download(
                    basename_of_gzipped_file,
                    gzipped_file_path,
                    self.configuration_for_cloud_file_storage.folder_id_of_parent_of_cloud_file_storage,
                )
            else:
                logger.warning("While trying to read visited campaign links, one has found that the cloud file storage configuration is invalid. Look for the main configuration file.")

        # Anyway, use local or downloaded one.
        # Gunzip
        try:
            self._decompress_file(gzipped_file_path, file_path)
        except FileNotFoundError:
            logger.warning(f"File not found: ({gzipped_file_path})")
            # Here, let's do not return. That means trying to read a plain text file.

        # Read visited URLs from file
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                self.visited_links = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_links = set()
        return self.visited_links

    def _write_visited_campaign_links_to_file(self):
        # Save the updated visited URLs to the file
        file_path = self._get_full_visited_urls_file_path()
        with open(file_path, "w", encoding="utf-8") as file:
            for url in self.visited_links:
                file.write(url + "\n")
        # Gzip
        gzipped_file_path = self._get_gzipped_full_visited_urls_file_path()
        self._compress_file(file_path, gzipped_file_path)
        logger.info(f"One has saved and gzipped: ({gzipped_file_path})")
        basename_of_gzipped_file = os.path.basename(gzipped_file_path)
        if self.flag_use_cloud_file_storage:
            # Upload
            if self.configuration_for_cloud_file_storage and self.configuration_for_cloud_file_storage.has_valid_cloud_file_storage_config():
                self.cloud_file_storage.upload(
                    basename_of_gzipped_file,
                    gzipped_file_path,
                    self.configuration_for_cloud_file_storage.folder_id_of_parent_of_cloud_file_storage,
                )
            else:
                logger.warning("While trying to write visited campaign links, one has found that the cloud file storage configuration is invalid. Look for the main configuration file.")

    def delete_all(self) -> None:
        file_path = self._get_full_visited_urls_file_path()
        gzipped_file_path = self._get_gzipped_full_visited_urls_file_path()
        logger.info(f"Deleting if exist: ({file_path}) and ({gzipped_file_path})...")
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
        try:
            os.remove(gzipped_file_path)
        except FileNotFoundError:
            pass
        basename_of_gzipped_file = os.path.basename(gzipped_file_path)
        if self.flag_use_cloud_file_storage:
            if self.configuration_for_cloud_file_storage and self.configuration_for_cloud_file_storage.has_valid_cloud_file_storage_config():
                self.cloud_file_storage.delete(
                    basename_of_gzipped_file,
                    self.configuration_for_cloud_file_storage.folder_id_of_parent_of_cloud_file_storage,
                )
            else:
                logger.warning("While trying to write visited campaign links, one has found that the cloud file storage configuration is invalid. Look for the main configuration file.")


class LinkVisitorClientContext:

    def __init__(self):
        self.driver = None  # It's a Selenium driver.

    def clean_up(self):
        if self.driver:
            self.driver.quit()


class LinkVisitor:

    def __init__(self):
        self.configuration_for_cloud_file_storage = None   # The lifecycle of this object is handled by this object.
        self.cloud_file_storage = CloudFileStorage()
        self.visited_campaign_link_recorder = VisitedCampaignLinkController()
        self.last_run_recorder = LastRunRecorder()
        self.flag_to_use_cloud_file_storage = False

    def init_with_global_config(self, global_config_ir: GlobalConfigIR) -> None:
        # Configuration about Cloud File Storage is very local to this class. It's for modularity.
        # Therefore, if one can, let's initialize it from `global_config.`
        # i.e. Initialize `self.configuration_for_cloud_file_storage` with the given configuration, if available.
        global_config = global_config_ir.raw_config
        self.flag_to_use_cloud_file_storage = False
        if "cloud_file_storage" in global_config:
            global_config_for_cloud_file_storage = global_config["cloud_file_storage"]
            if "enabled" in global_config_for_cloud_file_storage:
                value = global_config_for_cloud_file_storage["enabled"]
                if value:
                    self.flag_to_use_cloud_file_storage = True
            if "folder_id_for_parent" in global_config_for_cloud_file_storage:
                self.configuration_for_cloud_file_storage = ConfigurationForCloudFileStorage()
                self.configuration_for_cloud_file_storage.init_with_core_config(global_config_for_cloud_file_storage["folder_id_for_parent"])
        self.visited_campaign_link_recorder.init_with_cloud_file_storage(self.configuration_for_cloud_file_storage, self.cloud_file_storage)

    def visit_all(self, nid, npw, set_of_campaign_links: set[str]) -> None:
        # It creates a Naver session and visit campaign links.
        # 적립 확인 링크 - https://new-m.pay.naver.com/pointshistory/list?category=all
        logger.info(f"Creating a Naver session and visit pages with ID: ({nid}), if needed.")
        client_context = None

        # Reset this.
        self.visited_campaign_link_recorder.reset_with_nid(nid)

        self._prepare_visit(nid)
        client_context = self._visit(set_of_campaign_links, client_context, nid, npw)
        self._finish_visit(nid)

        if client_context:
            client_context.clean_up()

    def _prepare_visit(self, nid: str) -> None:
        self.visited_campaign_link_recorder.prepare_visit()
        self.last_run_recorder.prepare_visit(nid)

    def _finish_visit(self, nid: str) -> None:
        self.visited_campaign_link_recorder.finish_visit()
        self.last_run_recorder.finish_visit(nid)

    def _visit(
        self,
        set_of_campaign_links,
        client_context,
        nid,
        npw,
    ):
        for campaign_link in set_of_campaign_links:
            logger.info(f"Campaign link to visit: {campaign_link}")
        flag_use_cloud_file_storage = self.flag_to_use_cloud_file_storage
        logger.info(f"Use a cloud storage to manage a list of visited URLs? (True/False) {flag_use_cloud_file_storage}")
        self.visited_campaign_link_recorder.flag_use_cloud_file_storage = flag_use_cloud_file_storage

        for campaign_link in set_of_campaign_links:
            if self.visited_campaign_link_recorder.is_visited_campaign_link(campaign_link):
                continue  # Skip already visited links
            try:
                logger.info(f"Visiting a campaign link: {campaign_link}")
                client_context = lazy_init_client_context_if_needed(client_context, nid, npw)
                if not client_context:
                    return
                driver = client_context.driver
                driver.get(campaign_link)

                # Handle unexpected alerts
                try:
                    const_time_to_wait_in_sec = 3
                    WebDriverWait(driver, const_time_to_wait_in_sec).until(EC.alert_is_present()).accept()
                except (SC.NoAlertPresentException, SC.TimeoutException):
                    pass  # No alert present, continue

                if campaign_link.startswith("https://campaign2.naver.com/"):
                    const_time_to_wait_in_sec = 16
                    try:
                        WebDriverWait(driver, const_time_to_wait_in_sec).until(EC.presence_of_element_located((By.CLASS_NAME, "popup_link")))
                        element_to_go_to_the_next_step = driver.find_element(By.CLASS_NAME, "popup_link")
                        if element_to_go_to_the_next_step:
                            try:
                                element_to_go_to_the_next_step.click()
                            except SC.exceptions.ElementNotInteractableException:
                                pass
                            except SC.exceptions.StaleElementReferenceException:
                                pass
                    except SC.exceptions.TimeoutException:
                        pass

                self.visited_campaign_link_recorder.record_visit(campaign_link)
            except SC.exceptions.UnexpectedAlertPresentException:
                logger.warning(f"Unexpected alert on {campaign_link}, skipping...")

            WebDriverWait(driver, 5).until(lambda d: True)  # Acts as a non-blocking sleep

        return client_context



def create_link_visitor_client_context_with_selenium(nid, npw) -> LinkVisitorClientContext | None:
    """
    Create a LinkVisitorClientContext using Selenium with undetected-chromedriver.
    Returns the created LinkVisitorClientContext if successful, None otherwise.
    """
    try:
        driver = UC.Chrome()
    except selenium.common.exceptions.SessionNotCreatedException as e:
        logger.error(f"Selenium session could not be created. Please ensure that the Chrome browser is installed and compatible with the undetected-chromedriver version being used. Error details: {e}")
        return None

    driver.implicitly_wait(0.5)

    client_context = LinkVisitorClientContext()
    client_context.driver = driver

    login_result = visit_login_page(driver, nid, npw)
    if not login_result:
        logger.error(f"Failed to log in with ID: {nid}. Please check your credentials.")
        client_context.clean_up()
        return None

    return client_context


def wait_for_page_load(driver):
    while True:
        try:
            title = driver.title
            if title == "네이버페이" or title == "네이버":
                break
        except selenium.common.exceptions.NoSuchWindowException:
            logger.info("A user has closed the Chrome window.")
            sys.exit(-1)

        try:
            element_not_to_register_device = driver.find_element(by=By.ID, value="new.dontsave")
            if element_not_to_register_device:
                break
        except selenium.common.exceptions.NoSuchElementException:
            pass
        const_time_to_sleep_in_sec = 1
        time.sleep(const_time_to_sleep_in_sec)


def visit_login_page(driver, nid: str, npw: str) -> bool:
    """
    Visit the login page and perform login using the provided credentials.
    Returns True if login is successful, False otherwise.
    """

    logger.info("Visiting login page...")

    const_time_to_wait_in_sec = 16
    const_html_element_id_for_id = "id"
    const_html_element_id_for_password = "pw"
    const_html_element_id_for_submission = "log.login"
    const_login_page_url = "https://new-m.pay.naver.com/pcpay?page=1"

    driver.get(const_login_page_url)

    try:
        WebDriverWait(driver, const_time_to_wait_in_sec).until(EC.presence_of_element_located((By.ID, const_html_element_id_for_id)))
    except SC.exceptions.TimeoutException:
        logger.error("Timeout while waiting for the login page to load.")
        return False
    except SC.exceptions.NoSuchElementException:
        logger.error("Login page elements not found.")
        return False

    try:
        element_for_id = driver.find_element(by=By.ID, value=const_html_element_id_for_id)
    #     element_for_password = driver.find_element(by=By.ID, value=const_html_element_id_for_password)
    #     element_for_submission = driver.find_element(by=By.ID, value=const_html_element_id_for_submission)
    except SC.exceptions.NoSuchElementException as e:
        logger.error(f"Required elements for login not found: {e}")
        return False

    # try:
    #     # element_for_id.send_keys(nid)
    #     # element_for_password.send_keys(npw)
    #     # element_for_submission.click()
    # except SC.exceptions.ElementNotInteractableException as e:
    #     logger.error(f"Could not interact with login elements: {e}")
    #     return False

    wait_for_page_load(driver)

    try:
        element_not_to_register_device = driver.find_element(by=By.ID, value="new.dontsave")
        if element_not_to_register_device:
            element_not_to_register_device.click()
            wait_for_page_load(driver)
    except SC.exceptions.NoSuchElementException:
        pass
    return True


def create_link_visitor_client_context(nid, npw):
    return create_link_visitor_client_context_with_selenium(nid, npw)


def lazy_init_client_context_if_needed(client_context, nid, npw):
    if client_context:
        return client_context
    client_context = create_link_visitor_client_context(nid, npw)
    if not client_context:
        logger.error(f"Could not sign in with an ID: {nid}")
        return None
    return client_context
