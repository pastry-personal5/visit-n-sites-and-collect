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

    # selenium.common.exceptions
    exceptions_module = types.ModuleType("selenium.common.exceptions")
    for exc_name in [
        "NoSuchElementException",
        "SessionNotCreatedException",
        "NoSuchWindowException",
        "UnexpectedAlertPresentException",
        "ElementNotInteractableException",
        "StaleElementReferenceException",
    ]:
        setattr(exceptions_module, exc_name, type(exc_name, (_BaseSeleniumException,), {}))

    common_module = types.ModuleType("selenium.common")
    common_module.exceptions = exceptions_module

    # selenium.common as SC is also used with extra exception names.
    for exc_name in ["NoAlertPresentException", "TimeoutException"]:
        setattr(common_module, exc_name, type(exc_name, (_BaseSeleniumException,), {}))
    common_module.TimeoutException = getattr(common_module, "TimeoutException")
    common_module.NoAlertPresentException = getattr(common_module, "NoAlertPresentException")

    # selenium.webdriver.common.by
    by_module = types.ModuleType("selenium.webdriver.common.by")

    class By:
        CLASS_NAME = "class_name"
        ID = "id"

    by_module.By = By

    # selenium.webdriver.support.ui
    ui_module = types.ModuleType("selenium.webdriver.support.ui")

    class WebDriverWait:
        def __init__(self, *_args, **_kwargs):
            pass

        def until(self, *_args, **_kwargs):
            return None

    ui_module.WebDriverWait = WebDriverWait

    # selenium.webdriver.support.expected_conditions
    ec_module = types.ModuleType("selenium.webdriver.support.expected_conditions")

    def alert_is_present():
        return lambda _driver: False

    def presence_of_element_located(_locator):
        return lambda _driver: True

    ec_module.alert_is_present = alert_is_present
    ec_module.presence_of_element_located = presence_of_element_located

    # Package containers
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
        "visit_n_sites_and_collect",
        "visit_n_sites_and_collect.cloud_file_storage",
        "visit_n_sites_and_collect.configuration_for_cloud_file_storage",
        "visit_n_sites_and_collect.last_run_recorder",
        "visit_n_sites_and_collect.global_config",
        "visit_n_sites_and_collect.constants",
        "visit_n_sites_and_collect.link_visitor_user_info",
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
        _install_stub_module("visit_n_sites_and_collect")
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
            def __init__(self):
                self.folder_id = None

            def init_with_core_config(self, folder_id: str) -> None:
                self.folder_id = folder_id

            def has_valid_cloud_file_storage_config(self) -> bool:
                return bool(self.folder_id)

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
            "visit_n_sites_and_collect.cloud_file_storage",
            CloudFileStorage=_StubCloudFileStorage,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.configuration_for_cloud_file_storage",
            ConfigurationForCloudFileStorage=_StubConfigurationForCloudFileStorage,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.last_run_recorder",
            LastRunRecorder=_StubLastRunRecorder,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.global_config",
            GlobalConfigIR=_StubGlobalConfigIR,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.constants",
            Constants=_StubConstants,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.link_visitor_user_info",
            LinkVisitorUserInfo=lambda **kwargs: types.SimpleNamespace(**kwargs),
        )

        project_root = pathlib.Path(__file__).resolve().parents[1]
        module_path = project_root / "src" / "visit_n_sites_and_collect" / "link_visitor.py"
        spec = importlib.util.spec_from_file_location(
            "tests.link_visitor_under_test", module_path
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


class _RecorderSpy:
    def __init__(self):
        self.cloud_enabled_values = []
        self.init_calls = 0
        self.reset_calls = []
        self.prepare_calls = 0
        self.finish_calls = 0

    def init_with_cloud_file_storage(self, *_args, **_kwargs):
        self.init_calls += 1

    def set_use_cloud_file_storage(self, enabled: bool) -> None:
        self.cloud_enabled_values.append(bool(enabled))

    def reset_with_nid(self, nid: str) -> None:
        self.reset_calls.append(nid)

    def prepare_visit(self) -> None:
        self.prepare_calls += 1

    def finish_visit(self) -> None:
        self.finish_calls += 1

    def is_visited_campaign_link(self, _campaign_link: str) -> bool:
        return False

    def record_visit(self, _campaign_link: str) -> None:
        return None


class _LastRunRecorderSpy:
    def __init__(self):
        self.prepare_calls = []
        self.finish_calls = []

    def prepare_visit(self, user_id: str) -> None:
        self.prepare_calls.append(user_id)

    def finish_visit(self, user_id: str) -> None:
        self.finish_calls.append(user_id)


class _ClientContextSpy:
    def __init__(self):
        self.cleanup_calls = 0

    def clean_up(self) -> None:
        self.cleanup_calls += 1


class _DriverThatRaises:
    def get(self, _url: str) -> None:
        raise RuntimeError("boom")


class TestLinkVisitorCloudFlag(unittest.TestCase):
    def setUp(self):
        self.module = _import_link_visitor_module()

    def test_visited_campaign_link_controller_setter_toggles_flag(self):
        controller = self.module.VisitedCampaignLinkController()
        controller.set_use_cloud_file_storage(True)
        self.assertTrue(controller.flag_use_cloud_file_storage)
        controller.set_use_cloud_file_storage(False)
        self.assertFalse(controller.flag_use_cloud_file_storage)

    def test_init_with_global_config_propagates_cloud_flag_to_recorder(self):
        visitor = self.module.LinkVisitor()
        spy = _RecorderSpy()
        visitor.visited_campaign_link_recorder = spy

        global_config_ir = self.module.GlobalConfigIR(
            raw_config={
                "cloud_file_storage": {
                    "enabled": True,
                    "folder_id_for_parent": "FOLDER123",
                }
            }
        )
        visitor.init_with_global_config(global_config_ir)

        self.assertEqual(spy.init_calls, 1)
        self.assertEqual(spy.cloud_enabled_values, [True])

    def test_init_with_global_config_disables_cloud_flag_when_folder_missing(self):
        visitor = self.module.LinkVisitor()
        spy = _RecorderSpy()
        visitor.visited_campaign_link_recorder = spy

        global_config_ir = self.module.GlobalConfigIR(
            raw_config={"cloud_file_storage": {"enabled": True}}
        )
        visitor.init_with_global_config(global_config_ir)

        self.assertEqual(spy.init_calls, 1)
        self.assertEqual(spy.cloud_enabled_values, [False])

    def test_visit_method_propagates_cloud_flag_even_with_empty_links(self):
        visitor = self.module.LinkVisitor()
        spy = _RecorderSpy()
        visitor.visited_campaign_link_recorder = spy
        visitor.flag_to_use_cloud_file_storage = True

        link_visitor_user_info = self.module.LinkVisitorUserInfo(
            user_id="nid",
            user_pw="pw",
            flag_input_id_and_password_at_login=True,
        )
        result = visitor._visit(set(), None, link_visitor_user_info)

        self.assertIsNone(result)
        self.assertEqual(spy.cloud_enabled_values, [True])

    def test_visit_method_cleans_up_client_context_on_unexpected_error(self):
        visitor = self.module.LinkVisitor()
        recorder = _RecorderSpy()
        visitor.visited_campaign_link_recorder = recorder
        client_context = _ClientContextSpy()
        client_context.driver = _DriverThatRaises()
        link_visitor_user_info = self.module.LinkVisitorUserInfo(
            user_id="nid",
            user_pw="pw",
            flag_input_id_and_password_at_login=True,
        )

        original_lazy_init = self.module.lazy_init_client_context_if_needed
        self.module.lazy_init_client_context_if_needed = (
            lambda _client_context, _user_info: client_context
        )
        try:
            with self.assertRaisesRegex(RuntimeError, "boom"):
                visitor._visit(
                    {"https://campaign.example/a"},
                    None,
                    link_visitor_user_info,
                )
        finally:
            self.module.lazy_init_client_context_if_needed = original_lazy_init

        self.assertEqual(recorder.cloud_enabled_values, [False])
        self.assertEqual(client_context.cleanup_calls, 1)

    def test_visit_all_finishes_state_when_visit_raises(self):
        visitor = self.module.LinkVisitor()
        recorder = _RecorderSpy()
        last_run_recorder = _LastRunRecorderSpy()
        visitor.visited_campaign_link_recorder = recorder
        visitor.last_run_recorder = last_run_recorder
        visitor._visit = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom"))

        link_visitor_user_info = self.module.LinkVisitorUserInfo(
            user_id="nid",
            user_pw="pw",
            flag_input_id_and_password_at_login=True,
        )

        with self.assertRaisesRegex(RuntimeError, "boom"):
            visitor.visit_all(link_visitor_user_info, {"https://campaign.example/a"})

        self.assertEqual(recorder.reset_calls, ["nid"])
        self.assertEqual(recorder.prepare_calls, 1)
        self.assertEqual(recorder.finish_calls, 1)
        self.assertEqual(last_run_recorder.prepare_calls, ["nid"])
        self.assertEqual(last_run_recorder.finish_calls, ["nid"])


if __name__ == "__main__":
    unittest.main()
