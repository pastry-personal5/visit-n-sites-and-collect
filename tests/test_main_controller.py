import datetime
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


class _StubArticleLinkToCampaignLinkCache:
    pass


class _StubLinkVisitor:
    def __init__(self):
        self.init_calls = []
        self.visit_all_calls = []
        self.error_to_raise = None

    def init_with_global_config(self, global_config_ir):
        self.init_calls.append(global_config_ir)

    def visit_all(self, link_visitor_user_info, set_of_campaign_links):
        if self.error_to_raise is not None:
            raise self.error_to_raise
        self.visit_all_calls.append(
            (
                link_visitor_user_info.user_id,
                link_visitor_user_info.user_pw,
                set(set_of_campaign_links),
            )
        )


class _StubLastRunRecorder:
    dates_by_nid = {}

    def read_date_of_last_run(self, nid):
        return self.dates_by_nid.get(nid)


class _StubLinkFinderBase:
    instances = []
    result = set()

    def __init__(self, cache):
        self.cache = cache
        self.initialize_calls = []
        self.days_arguments = []
        self.cleanup_calls = 0
        self.__class__.instances.append(self)

    def initialize_with_config(self, prefixes):
        self.initialize_calls.append(prefixes)

    def find_set_of_campaign_links(self, days_difference_since_last_run):
        self.days_arguments.append(days_difference_since_last_run)
        return set(self.__class__.result)

    def cleanup(self):
        self.cleanup_calls += 1


class _StubLinkFinderForC1WebSiteImpl(_StubLinkFinderBase):
    instances = []
    result = set()


class _StubLinkFinderForD1WebSiteImpl(_StubLinkFinderBase):
    instances = []
    result = set()


def _import_main_module():
    stubbed_module_names = [
        "visit_n_sites_and_collect",
        "visit_n_sites_and_collect.article_link_to_campaign_link_cache",
        "visit_n_sites_and_collect.last_run_recorder",
        "visit_n_sites_and_collect.link_finder_for_c1_web_site_impl",
        "visit_n_sites_and_collect.link_finder_for_d1_web_site_impl",
        "visit_n_sites_and_collect.link_visitor",
        "visit_n_sites_and_collect.global_config",
        "visit_n_sites_and_collect.link_finder_impl_base",
        "visit_n_sites_and_collect.link_visitor_user_info",
    ]
    saved_modules = {name: sys.modules.get(name) for name in stubbed_module_names}
    if "loguru" not in sys.modules:
        logger = types.SimpleNamespace(
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
        )
        _install_stub_module("loguru", logger=logger)

    try:
        _install_stub_module("visit_n_sites_and_collect")
        _install_stub_module(
            "visit_n_sites_and_collect.article_link_to_campaign_link_cache",
            ArticleLinkToCampaignLinkCache=_StubArticleLinkToCampaignLinkCache,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.last_run_recorder",
            LastRunRecorder=_StubLastRunRecorder,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.link_finder_for_c1_web_site_impl",
            LinkFinderForC1WebSiteImpl=_StubLinkFinderForC1WebSiteImpl,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.link_finder_for_d1_web_site_impl",
            LinkFinderForD1WebSiteImpl=_StubLinkFinderForD1WebSiteImpl,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.link_visitor",
            LinkVisitor=_StubLinkVisitor,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.global_config",
            GlobalConfigController=object,
            GlobalConfigIR=type("GlobalConfigIR", (), {}),
        )
        _install_stub_module(
            "visit_n_sites_and_collect.link_finder_impl_base",
            LinkFinderImplBase=object,
        )
        _install_stub_module(
            "visit_n_sites_and_collect.link_visitor_user_info",
            LinkVisitorUserInfo=lambda **kwargs: types.SimpleNamespace(**kwargs),
        )

        project_root = pathlib.Path(__file__).resolve().parents[1]
        module_path = project_root / "src" / "visit_n_sites_and_collect" / "main.py"
        spec = importlib.util.spec_from_file_location(
            "tests.main_controller_under_test", module_path
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


class TestMainController(unittest.TestCase):
    def setUp(self):
        _StubLinkFinderForC1WebSiteImpl.instances = []
        _StubLinkFinderForD1WebSiteImpl.instances = []
        _StubLinkFinderForC1WebSiteImpl.result = set()
        _StubLinkFinderForD1WebSiteImpl.result = set()
        _StubLastRunRecorder.dates_by_nid = {}
        self.module = _import_main_module()

    def test_init_with_global_config_builds_only_enabled_collectors(self):
        controller = self.module.MainController()
        global_config_ir = types.SimpleNamespace(
            raw_config={"campaign_link_prefixes": ["https://campaign.example/"]},
            finders={
                "c1": {"enabled": True},
                "d1": {"enabled": False},
            },
        )

        controller._init_with_global_config(global_config_ir)

        self.assertEqual(controller.link_visitor.init_calls, [global_config_ir])
        self.assertEqual(len(controller.link_finders), 1)
        self.assertIsInstance(
            controller.link_finders[0], _StubLinkFinderForC1WebSiteImpl
        )
        self.assertEqual(
            controller.link_finders[0].initialize_calls,
            [["https://campaign.example/"]],
        )

    def test_find_and_visit_all_with_global_config_visits_union_for_each_user(self):
        controller = self.module.MainController()
        _StubLinkFinderForC1WebSiteImpl.result = {
            "https://campaign.example/a",
            "https://campaign.example/shared",
        }
        _StubLinkFinderForD1WebSiteImpl.result = {
            "https://campaign.example/b",
            "https://campaign.example/shared",
        }
        _StubLastRunRecorder.dates_by_nid = {
            "user1": datetime.date.today() - datetime.timedelta(days=2),
            "user2": datetime.date.today() - datetime.timedelta(days=2),
        }
        global_config_ir = types.SimpleNamespace(
            raw_config={
                "campaign_link_prefixes": ["https://campaign.example/"],
                "users": [
                    {
                        "id": "user1",
                        "pw": "pw1",
                        "flag_input_id_and_password_at_login": True,
                    },
                    {
                        "id": "user2",
                        "pw": "pw2",
                        "flag_input_id_and_password_at_login": True,
                    },
                ],
            },
            finders={
                "c1": {"enabled": True},
                "d1": {"enabled": True},
            },
        )

        controller.find_and_visit_all_with_global_config(global_config_ir)

        self.assertEqual(
            _StubLinkFinderForC1WebSiteImpl.instances[0].days_arguments, [2, 2]
        )
        self.assertEqual(
            _StubLinkFinderForD1WebSiteImpl.instances[0].days_arguments, [2, 2]
        )
        self.assertEqual(
            controller.link_visitor.visit_all_calls,
            [
                (
                    "user1",
                    "pw1",
                    {
                        "https://campaign.example/a",
                        "https://campaign.example/b",
                        "https://campaign.example/shared",
                    },
                ),
                (
                    "user2",
                    "pw2",
                    {
                        "https://campaign.example/a",
                        "https://campaign.example/b",
                        "https://campaign.example/shared",
                    },
                ),
            ],
        )

    def test_find_and_visit_all_with_global_config_cleans_up_collectors_on_error(self):
        controller = self.module.MainController()
        controller.link_visitor.error_to_raise = RuntimeError("boom")
        global_config_ir = types.SimpleNamespace(
            raw_config={
                "campaign_link_prefixes": ["https://campaign.example/"],
                "users": [
                    {
                        "id": "user1",
                        "pw": "pw1",
                        "flag_input_id_and_password_at_login": True,
                    }
                ],
            },
            finders={
                "c1": {"enabled": True},
                "d1": {"enabled": True},
            },
        )

        with self.assertRaisesRegex(RuntimeError, "boom"):
            controller.find_and_visit_all_with_global_config(global_config_ir)

        self.assertEqual(
            [finder.cleanup_calls for finder in _StubLinkFinderForC1WebSiteImpl.instances],
            [1],
        )
        self.assertEqual(
            [finder.cleanup_calls for finder in _StubLinkFinderForD1WebSiteImpl.instances],
            [1],
        )
        self.assertEqual(controller.link_finders, [])


if __name__ == "__main__":
    unittest.main()
