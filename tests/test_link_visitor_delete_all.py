import importlib.util
import os
import pathlib
import sys
import tempfile
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
        "SessionNotCreatedException",
        "NoSuchWindowException",
        "UnexpectedAlertPresentException",
    ]:
        setattr(exceptions_module, exc_name, type(exc_name, (_BaseSeleniumException,), {}))

    common_module = types.ModuleType("selenium.common")
    common_module.exceptions = exceptions_module

    for exc_name in ["NoAlertPresentException", "TimeoutException"]:
        setattr(common_module, exc_name, type(exc_name, (_BaseSeleniumException,), {}))

    by_module = types.ModuleType("selenium.webdriver.common.by")

    class By:
        CLASS_NAME = "class_name"

    by_module.By = By

    ui_module = types.ModuleType("selenium.webdriver.support.ui")

    class WebDriverWait:
        def __init__(self, *_args, **_kwargs):
            pass

        def until(self, *_args, **_kwargs):
            return None

    ui_module.WebDriverWait = WebDriverWait

    ec_module = types.ModuleType("selenium.webdriver.support.expected_conditions")

    def alert_is_present():
        return lambda _driver: False

    def presence_of_element_located(_locator):
        return lambda _driver: True

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
    if "loguru" not in sys.modules:
        logger = types.SimpleNamespace(
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
            exception=lambda *args, **kwargs: None,
        )
        _install_stub_module("loguru", logger=logger)

    _install_selenium_stubs()

    class _DummyDriver:
        def implicitly_wait(self, *_args, **_kwargs):
            return None

    _install_stub_module(
        "undetected_chromedriver",
        Chrome=lambda *args, **kwargs: _DummyDriver(),
    )

    class _StubCloudFileStorage:
        pass

    class _StubConfigurationForCloudFileStorage:
        def has_valid_cloud_file_storage_config(self) -> bool:
            return False

    class _StubLastRunRecorder:
        def prepare_visit(self, *_args, **_kwargs):
            return None

        def finish_visit(self, *_args, **_kwargs):
            return None

    class _StubGlobalConfigIR:
        def __init__(self, raw_config):
            self.raw_config = raw_config

    class _StubConstants:
        data_dir_path = "."

    _install_stub_module(
        "src.visit_n_sites_and_collect.cloud_file_storage",
        CloudFileStorage=_StubCloudFileStorage,
    )
    _install_stub_module(
        "src.visit_n_sites_and_collect.configuration_for_cloud_file_storage",
        ConfigurationForCloudFileStorage=_StubConfigurationForCloudFileStorage,
    )
    _install_stub_module(
        "src.visit_n_sites_and_collect.last_run_recorder",
        LastRunRecorder=_StubLastRunRecorder,
    )
    _install_stub_module(
        "src.visit_n_sites_and_collect.global_config",
        GlobalConfigIR=_StubGlobalConfigIR,
    )
    _install_stub_module(
        "src.visit_n_sites_and_collect.constants",
        Constants=_StubConstants,
    )

    project_root = pathlib.Path(__file__).resolve().parents[1]
    module_path = project_root / "src" / "visit_n_sites_and_collect" / "link_visitor.py"
    spec = importlib.util.spec_from_file_location(
        "tests.link_visitor_delete_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestVisitedCampaignLinkControllerDeleteAll(unittest.TestCase):
    def setUp(self):
        self.module = _import_link_visitor_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.module.Constants.data_dir_path = self.temp_dir.name

    def test_delete_all_removes_gz_even_if_plain_text_missing(self):
        controller = self.module.VisitedCampaignLinkController()
        controller.set_use_cloud_file_storage(False)
        controller.reset_with_nid("user1")

        gz_path = os.path.join(self.temp_dir.name, "visited_urls.user1.txt.gz")
        with open(gz_path, "wb") as f:
            f.write(b"not-a-real-gzip-but-fine")

        self.assertFalse(os.path.exists(os.path.join(self.temp_dir.name, "visited_urls.user1.txt")))
        self.assertTrue(os.path.exists(gz_path))

        controller.delete_all()

        self.assertFalse(os.path.exists(gz_path))

    def test_delete_all_removes_both_files_when_present(self):
        controller = self.module.VisitedCampaignLinkController()
        controller.set_use_cloud_file_storage(False)
        controller.reset_with_nid("user2")

        txt_path = os.path.join(self.temp_dir.name, "visited_urls.user2.txt")
        gz_path = os.path.join(self.temp_dir.name, "visited_urls.user2.txt.gz")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("https://example.com\n")
        with open(gz_path, "wb") as f:
            f.write(b"data")

        controller.delete_all()

        self.assertFalse(os.path.exists(txt_path))
        self.assertFalse(os.path.exists(gz_path))


if __name__ == "__main__":
    unittest.main()

