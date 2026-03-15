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


class _StubVisitedCampaignLinkController:
    def __init__(self):
        self.use_cloud_storage_values = []
        self.init_with_cloud_file_storage_calls = []
        self.reset_nids = []
        self.delete_all_calls = 0

    def init_with_cloud_file_storage(self, configuration_for_cloud_file_storage, cloud_file_storage):
        self.init_with_cloud_file_storage_calls.append(
            (configuration_for_cloud_file_storage, cloud_file_storage)
        )

    def set_use_cloud_file_storage(self, enabled: bool) -> None:
        self.use_cloud_storage_values.append(bool(enabled))

    def reset_with_nid(self, nid: str) -> None:
        self.reset_nids.append(nid)

    def delete_all(self) -> None:
        self.delete_all_calls += 1


class _StubCloudFileStorage:
    pass


class _StubConfigurationForCloudFileStorage:
    def __init__(self):
        self.folder_id = None

    def init_with_core_config(self, folder_id: str) -> None:
        self.folder_id = folder_id


def _import_clean_visited_urls_module():
    if "loguru" not in sys.modules:
        logger = types.SimpleNamespace(
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
        )
        _install_stub_module("loguru", logger=logger)

    _install_stub_module(
        "src.visit_n_sites_and_collect.cloud_file_storage",
        CloudFileStorage=_StubCloudFileStorage,
    )
    _install_stub_module(
        "src.visit_n_sites_and_collect.configuration_for_cloud_file_storage",
        ConfigurationForCloudFileStorage=_StubConfigurationForCloudFileStorage,
    )
    _install_stub_module(
        "src.visit_n_sites_and_collect.link_visitor",
        VisitedCampaignLinkController=_StubVisitedCampaignLinkController,
    )
    _install_stub_module(
        "src.visit_n_sites_and_collect.global_config",
        GlobalConfigController=object,
        GlobalConfigIR=object,
    )

    project_root = pathlib.Path(__file__).resolve().parents[1]
    module_path = project_root / "src" / "visit_n_sites_and_collect" / "clean_visited_urls.py"
    spec = importlib.util.spec_from_file_location(
        "tests.clean_visited_urls_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestCleaningControllerCloudFlagPropagation(unittest.TestCase):
    def setUp(self):
        self.module = _import_clean_visited_urls_module()

    def test_cleanup_sets_cloud_flag_false_when_disabled(self):
        controller = self.module.CleaningController()

        global_config_ir = types.SimpleNamespace(
            raw_config={
                "cloud_file_storage": {"enabled": False},
                "users": [{"id": "user1"}, {"id": "user2"}],
            }
        )
        controller.delete_all(global_config_ir)

        visited = controller.visited_campaign_link_controller
        self.assertEqual(visited.use_cloud_storage_values, [False])
        self.assertEqual(len(visited.init_with_cloud_file_storage_calls), 1)
        self.assertEqual(visited.reset_nids, ["user1", "user2"])
        self.assertEqual(visited.delete_all_calls, 2)

    def test_cleanup_sets_cloud_flag_true_when_enabled_even_without_folder(self):
        controller = self.module.CleaningController()

        global_config_ir = types.SimpleNamespace(
            raw_config={
                "cloud_file_storage": {"enabled": True},
                "users": [{"id": "user1"}],
            }
        )
        controller.delete_all(global_config_ir)

        visited = controller.visited_campaign_link_controller
        self.assertEqual(visited.use_cloud_storage_values, [True])
        (config_obj, cloud_obj) = visited.init_with_cloud_file_storage_calls[0]
        self.assertIsNone(config_obj)
        self.assertIsInstance(cloud_obj, _StubCloudFileStorage)

    def test_cleanup_passes_configuration_when_folder_id_present(self):
        controller = self.module.CleaningController()

        global_config_ir = types.SimpleNamespace(
            raw_config={
                "cloud_file_storage": {
                    "enabled": True,
                    "folder_id_for_parent": "FOLDER123",
                },
                "users": [{"id": "user1"}],
            }
        )
        controller.delete_all(global_config_ir)

        visited = controller.visited_campaign_link_controller
        self.assertEqual(visited.use_cloud_storage_values, [True])
        (config_obj, _cloud_obj) = visited.init_with_cloud_file_storage_calls[0]
        self.assertIsNotNone(config_obj)
        self.assertEqual(getattr(config_obj, "folder_id", None), "FOLDER123")


if __name__ == "__main__":
    unittest.main()

