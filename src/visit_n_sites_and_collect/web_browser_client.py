import selenium
import undetected_chromedriver as UC
from loguru import logger
from selenium.common.exceptions import WebDriverException


class WebBrowserClient():
    def __init__(self):
        self.driver = None

    def prepare(self) -> None:
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            self.driver = UC.Chrome(driver_executable_path=ChromeDriverManager().install())
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
