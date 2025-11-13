import importlib.util
import pathlib
import sys
import types
import unittest


def _stub_missing_dependencies():
    """Inject minimal stand-ins for optional third-party modules."""

    if "loguru" not in sys.modules:
        logger = types.SimpleNamespace(
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
        )
        sys.modules["loguru"] = types.SimpleNamespace(logger=logger)

_stub_missing_dependencies()
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
PUBLISHER_MODULE_PATH = PROJECT_ROOT / "src" / "visit_n_sites_and_collect" / "publisher.py"
SPEC = importlib.util.spec_from_file_location(
    "tests.publisher_under_test", PUBLISHER_MODULE_PATH
)
publisher_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = publisher_module
SPEC.loader.exec_module(publisher_module)
PublisherController = publisher_module.PublisherController


class TestPublisherController(unittest.TestCase):
    def setUp(self):
        self.controller = PublisherController()

    def test_create_publisher_links_to_visit_respects_day_difference(self):
        target_base_url_list = ["https://example.com"]
        template_list = ["https://example.com/page=%d"]

        result = self.controller.create_publisher_links_to_visit(
            target_base_url_list, template_list, 5
        )

        self.assertEqual(
            result,
            [
                "https://example.com",
                "https://example.com/page=1",
                "https://example.com/page=2",
                "https://example.com/page=3",
                "https://example.com/page=4",
                "https://example.com/page=5",
            ],
        )

    def test_create_publisher_links_to_visit_limits_to_max_pages(self):
        target_base_url_list = ["https://example.com"]
        template_list = ["https://example.com/page=%d"]

        result = self.controller.create_publisher_links_to_visit(
            target_base_url_list, template_list, 25
        )

        # const_max_page_index=10, so expect base + 10 numbered pages
        self.assertEqual(result[0], "https://example.com")
        self.assertEqual(len(result), 11)
        self.assertEqual(result[-1], "https://example.com/page=10")

    def test_create_publisher_links_to_visit_handles_unknown_last_run(self):
        target_base_url_list = ["https://example.com"]
        template_list = ["https://example.com/page=%d"]

        result = self.controller.create_publisher_links_to_visit(
            target_base_url_list, template_list, -1
        )

        self.assertEqual(
            result,
            [
                "https://example.com",
                "https://example.com/page=1",
            ],
        )

    def test_create_publisher_links_to_visit_handles_multiple_publishers(self):
        target_base_url_list = [
            "https://example.com",
            "https://example.org",
        ]
        template_list = [
            "https://example.com/page=%d",
            "https://example.org/page=%d",
        ]

        result = self.controller.create_publisher_links_to_visit(
            target_base_url_list, template_list, 2
        )

        self.assertEqual(
            result,
            [
                "https://example.com",
                "https://example.com/page=1",
                "https://example.com/page=2",
                "https://example.org",
                "https://example.org/page=1",
                "https://example.org/page=2",
            ],
        )

    def test_create_publisher_links_to_visit_requires_matching_lengths(self):
        with self.assertRaises(AssertionError):
            self.controller.create_publisher_links_to_visit(
                ["https://example.com"],
                ["https://example.com/page=%d", "https://example.org/page=%d"],
                1,
            )


if __name__ == "__main__":
    unittest.main()
