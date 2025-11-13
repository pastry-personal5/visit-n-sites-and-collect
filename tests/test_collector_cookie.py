import datetime
import os
import sys
import tempfile
import types
import unittest


if "loguru" not in sys.modules:
    logger = types.SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
    )
    sys.modules["loguru"] = types.SimpleNamespace(logger=logger)

if "bs4" not in sys.modules:
    class _BeautifulSoup:  # pragma: no cover - simple stub
        def __init__(self, *args, **kwargs):
            pass

        def find_all(self, *args, **kwargs):
            return []

    sys.modules["bs4"] = types.SimpleNamespace(BeautifulSoup=_BeautifulSoup)

if "selenium" not in sys.modules:
    class _WebDriverException(Exception):
        pass

    selenium_module = types.ModuleType("selenium")
    webdriver_module = types.ModuleType("selenium.webdriver")
    common_module = types.ModuleType("selenium.common")
    exceptions_module = types.ModuleType("selenium.common.exceptions")
    exceptions_module.WebDriverException = _WebDriverException
    common_module.exceptions = exceptions_module
    selenium_module.webdriver = webdriver_module
    selenium_module.common = common_module
    sys.modules["selenium"] = selenium_module
    sys.modules["selenium.webdriver"] = webdriver_module
    sys.modules["selenium.common"] = common_module
    sys.modules["selenium.common.exceptions"] = exceptions_module

if "undetected_chromedriver" not in sys.modules:
    class _DummyDriver:
        def __init__(self):
            self.page_source = ""

        def implicitly_wait(self, *_args, **_kwargs):
            return None

        def quit(self):
            return None

        def get(self, *_args, **_kwargs):
            return None

    sys.modules["undetected_chromedriver"] = types.SimpleNamespace(Chrome=_DummyDriver)

from src.visit_n_sites_and_collect.collector_cookie import CollectorCookie, CollectorCookieController
from src.visit_n_sites_and_collect.constants import Constants


class TestCollectorCookieController(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp_dir.cleanup)
        self._original_data_dir = Constants.data_dir_path
        Constants.data_dir_path = self._temp_dir.name
        self.controller = CollectorCookieController()

    def tearDown(self):
        Constants.data_dir_path = self._original_data_dir

    def test_create_cookie_file_path_uses_configured_data_dir(self):
        path = self.controller._create_cookie_file_path("some_user")

        expected = os.path.join(self._temp_dir.name, "some_user.cookie.yaml")
        self.assertEqual(path, expected)

    def test_write_then_read_cookie_round_trip(self):
        cookie = CollectorCookie("tester", datetime.date(2024, 9, 7))

        self.controller.write_cookie(cookie)
        loaded = self.controller.read_cookie("tester")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.nid, "tester")
        self.assertEqual(loaded.date_of_last_run, datetime.date(2024, 9, 7))

    def test_read_cookie_returns_none_when_file_missing(self):
        self.assertIsNone(self.controller.read_cookie("unknown"))


if __name__ == "__main__":
    unittest.main()
