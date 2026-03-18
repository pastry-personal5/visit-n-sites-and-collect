import importlib.util
import pathlib
import sys
import types
import unittest


def _install_stub_module(name: str, **attrs) -> None:
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


def _install_selenium_stubs() -> None:
    class _BaseSeleniumException(Exception):
        pass

    exceptions_module = types.ModuleType("selenium.common.exceptions")
    for exc_name in [
        "NoSuchElementException",
        "SessionNotCreatedException",
        "NoSuchWindowException",
        "UnexpectedAlertPresentException",
        "ElementNotInteractableException",
        "StaleElementReferenceException",
        "TimeoutException",
        "NoAlertPresentException",
    ]:
        setattr(exceptions_module, exc_name, type(exc_name, (_BaseSeleniumException,), {}))

    common_module = types.ModuleType("selenium.common")
    common_module.exceptions = exceptions_module
    common_module.TimeoutException = exceptions_module.TimeoutException
    common_module.NoAlertPresentException = exceptions_module.NoAlertPresentException

    by_module = types.ModuleType("selenium.webdriver.common.by")

    class By:
        CLASS_NAME = "class_name"
        ID = "id"

    by_module.By = By

    ui_module = types.ModuleType("selenium.webdriver.support.ui")

    class WebDriverWait:
        def __init__(self, driver, *_args, **_kwargs):
            self.driver = driver

        def until(self, condition, *_args, **_kwargs):
            return condition(self.driver)

    ui_module.WebDriverWait = WebDriverWait

    ec_module = types.ModuleType("selenium.webdriver.support.expected_conditions")

    def alert_is_present():
        return lambda _driver: False

    def presence_of_element_located(locator):
        by, value = locator

        def _predicate(driver):
            return driver.find_element(by=by, value=value)

        return _predicate

    ec_module.alert_is_present = alert_is_present
    ec_module.presence_of_element_located = presence_of_element_located

    webdriver_common_module = types.ModuleType("selenium.webdriver.common")
    webdriver_support_module = types.ModuleType("selenium.webdriver.support")
    webdriver_module = types.ModuleType("selenium.webdriver")

    selenium_module = types.ModuleType("selenium")
    selenium_module.common = common_module
    selenium_module.webdriver = webdriver_module

    sys.modules["selenium"] = selenium_module
    sys.modules["selenium.common"] = common_module
    sys.modules["selenium.common.exceptions"] = exceptions_module
    sys.modules["selenium.webdriver"] = webdriver_module
    sys.modules["selenium.webdriver.common"] = webdriver_common_module
    sys.modules["selenium.webdriver.common.by"] = by_module
    sys.modules["selenium.webdriver.support"] = webdriver_support_module
    sys.modules["selenium.webdriver.support.ui"] = ui_module
    sys.modules["selenium.webdriver.support.expected_conditions"] = ec_module


def _import_link_visitor_module():
    stubbed_module_names = [
        "visit_n_sites_and_collect.cloud_file_storage",
        "visit_n_sites_and_collect.configuration_for_cloud_file_storage",
        "visit_n_sites_and_collect.last_run_recorder",
        "visit_n_sites_and_collect.global_config",
        "visit_n_sites_and_collect.constants",
    ]
    saved_modules = {name: sys.modules.get(name) for name in stubbed_module_names}
    if "loguru" not in sys.modules:
        logger = types.SimpleNamespace(
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
            exception=lambda *args, **kwargs: None,
        )
        _install_stub_module("loguru", logger=logger)

    _install_selenium_stubs()

    try:
        class _DummyDriver:
            def implicitly_wait(self, *_args, **_kwargs):
                return None

        _install_stub_module(
            "undetected_chromedriver",
            Chrome=lambda *args, **kwargs: _DummyDriver(),
        )
        _install_stub_module(
            "visit_n_sites_and_collect.cloud_file_storage",
            CloudFileStorage=type("CloudFileStorage", (), {}),
        )
        _install_stub_module(
            "visit_n_sites_and_collect.configuration_for_cloud_file_storage",
            ConfigurationForCloudFileStorage=type(
                "ConfigurationForCloudFileStorage",
                (),
                {"has_valid_cloud_file_storage_config": lambda self: False},
            ),
        )
        _install_stub_module(
            "visit_n_sites_and_collect.last_run_recorder",
            LastRunRecorder=type("LastRunRecorder", (), {}),
        )
        _install_stub_module(
            "visit_n_sites_and_collect.global_config",
            GlobalConfigIR=type("GlobalConfigIR", (), {}),
        )
        _install_stub_module(
            "visit_n_sites_and_collect.constants",
            Constants=type("Constants", (), {"data_dir_path": "."}),
        )

        project_root = pathlib.Path(__file__).resolve().parents[1]
        module_path = project_root / "src" / "visit_n_sites_and_collect" / "link_visitor.py"
        spec = importlib.util.spec_from_file_location(
            "tests.link_visitor_login_under_test", module_path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for name, saved in saved_modules.items():
            if saved is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = saved


class _FakeElement:
    def __init__(self):
        self.sent_values = []
        self.click_count = 0

    def send_keys(self, value):
        self.sent_values.append(value)

    def click(self):
        self.click_count += 1


class _FakeDriver:
    def __init__(self, elements):
        self.elements = elements
        self.get_calls = []

    def get(self, url):
        self.get_calls.append(url)

    def find_element(self, by=None, value=None):
        key = (by, value)
        if key not in self.elements:
            raise self._no_such_element(f"Missing element: {key}")
        return self.elements[key]


class TestVisitLoginPage(unittest.TestCase):
    def setUp(self):
        self.module = _import_link_visitor_module()

    def test_visit_login_page_submits_credentials_and_dismisses_device_prompt(self):
        field_id = _FakeElement()
        field_password = _FakeElement()
        submit_button = _FakeElement()
        device_prompt = _FakeElement()

        driver = _FakeDriver(
            {
                (self.module.By.ID, "id"): field_id,
                (self.module.By.ID, "pw"): field_password,
                (self.module.By.ID, "log.login"): submit_button,
                (self.module.By.ID, "new.dontsave"): device_prompt,
            }
        )
        driver._no_such_element = self.module.SC.exceptions.NoSuchElementException

        wait_for_page_load_calls = []
        self.module.wait_for_page_load = lambda seen_driver: wait_for_page_load_calls.append(
            seen_driver
        )

        result = self.module.visit_login_page(driver, "user1", "pw1")

        self.assertTrue(result)
        self.assertEqual(
            driver.get_calls, ["https://new-m.pay.naver.com/pcpay?page=1"]
        )
        self.assertEqual(field_id.sent_values, ["user1"])
        self.assertEqual(field_password.sent_values, ["pw1"])
        self.assertEqual(submit_button.click_count, 1)
        self.assertEqual(device_prompt.click_count, 1)
        self.assertEqual(wait_for_page_load_calls, [driver, driver])

    def test_visit_login_page_returns_false_when_initial_wait_times_out(self):
        timeout_exception = self.module.SC.exceptions.TimeoutException

        class _TimeoutWait:
            def __init__(self, *_args, **_kwargs):
                pass

            def until(self, *_args, **_kwargs):
                raise timeout_exception()

        driver = _FakeDriver({})
        driver._no_such_element = self.module.SC.exceptions.NoSuchElementException
        self.module.WebDriverWait = _TimeoutWait

        result = self.module.visit_login_page(driver, "user1", "pw1")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
