# -*- coding: utf-8 -*-
from loguru import logger
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

def read_global_config() -> dict:
    """Read a global configuration.

    Returns:
        dict: a user configuration dictionary.
            Currently, its format is YAML and it looks like this below.
            Please note that two spaces are recommended.

            users:
                - id:
                    foo
                pw:
                    bar
                ...
    """
    config_file_path = "./global_config.yaml"
    try:
        f = open(config_file_path, "r", encoding="utf-8")
        global_config = yaml.load(f.read(), Loader=Loader)
    except IOError:
        logger.error(f"Could not read file: {config_file_path}")
        return {}
    return global_config
