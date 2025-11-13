# -*- coding: utf-8 -*-
import sys

from loguru import logger
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class GlobalConfigIR:

    def __init__(self):
        self.config = {}


class GlobalConfigController:

    def __init__(self):
        self.config_validators = [
            UserConfigValidator(),
        ]

    def validate(self, global_config: GlobalConfigIR) -> bool:
        for validator in self.config_validators:
            if not validator.validate(global_config):
                logger.error(f"Validation failed for {validator.__class__.__name__}. Please check the configuration file and ensure all required fields are correctly set.")
                return False
        return True

    def read_global_config(self) -> GlobalConfigIR:
        # An object of GlobalConfigIR is created and returned.
        # The object is initialized with the content of the global_config.yaml file.
        try:
            with open("./config/global_config.yaml", "r", encoding="utf-8") as config_file_stream:
                global_config_dict = yaml.safe_load(config_file_stream)
                global_config = GlobalConfigIR()
                global_config.config = global_config_dict
                return global_config
        except FileNotFoundError:
            logger.error("The global_config.yaml file was not found. Please ensure the file exists in the project root directory.")
            sys.exit(-1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing the global_config.yaml file: {e}. Please ensure the file is properly formatted YAML.")
            sys.exit(-1)
        except IOError as e:
            logger.error(f"An IOError occurred while reading the global_config.yaml file: {e}. Please check file permissions and try again.")
            sys.exit(-1)


class ConfigValidatorBase:

    def __init__(self):
        pass

    def validate(self, global_config: GlobalConfigIR) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")


class UserConfigValidator(ConfigValidatorBase):

    def __init__(self):
        super().__init__()

    def validate(self, global_config: GlobalConfigIR) -> bool:
        try:
            users = global_config.config['users']
            for user in users:
                if "id" not in user:
                    logger.error("user id in configuration not found.")
                    return False
                if "pw" not in user:
                    logger.error("user id in configuration not found.")
                    return False
        except KeyError:
            logger.error("users in configuration not found.")
            return False
        return True
