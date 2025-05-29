#!/usr/bin/env python3
import argparse
import logging
import os
import yaml

from diff_config import YAML_CONFIG_PATH, API_URLS

BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
ENDC = '\033[0m'


class DiffCommon:
    def diff_cmdline(self):
        """
        Method parses commandline input and shows help message if needed.
        """
        description = (
            "Tool creates report describing differences between Google Cloud"
            " APIs fields and resources integrated in"
            " terraform-provider-google and terraform-provider-google-beta."
        )
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument(
            "-t",
            "--terraform_config",
            help="Path to the terraform config main.tf file",
            required=True
        )
        parser.add_argument(
            "-a",
            "--api",
            choices=API_URLS.keys(),
            default="compute",
            help="The Google API that will be analyzed"
        )
        parser.add_argument(
            "-s",
            "--save_file",
            action="store_true",
            help="Save API and Terraform component schemas as a JSON files"
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Increase logs verbosity level"
        )
        return parser

    def diff_log(self, verbose=False):
        """
        Method creates logging system for the tool.

                Create logger based on the verbosity level.

        Args:
            verbose (bool): If True, logging level is set to DEBUG; otherwise
            set it to INFO.
        """
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        self.log = logging.getLogger(__name__)

    def load_config_diff_report(self):
        """
        Loads and parses the YAML configuration file for the diff report.

        Returns:
            bool:
                - `True` if the YAML configuration is successfully loaded
                  and parsed.
                - `False` if loading or parsing the YAML configuration fails.
        """
        with open(YAML_CONFIG_PATH, "r") as yaml_config:
            self.yaml_config = yaml.safe_load(yaml_config)
        if not self.yaml_config:
            self.log.error("Getting YAML config failed!")
            return False
        return True

    def change_to_tf_dir(self):
        """
        Changes the current working directory to the Terraform configuration
        directory specified by `tf_config_path`.

        Returns:
            bool: True if the directory was successfully changed and 'main.tf'
                       was found,
                  False if 'main.tf' was not found in the specified directory.
        """
        if not os.path.isabs(self.tf_config_path):
            self.tf_config_path = os.path.join(
                os.getcwd(),
                self.tf_config_path
            )

        if not os.path.exists(os.path.join(self.tf_config_path, "main.tf")):
            self.log.error("Wrong main.tf terraform path!")
            return False

        self.cwd = os.getcwd()
        os.chdir(self.tf_config_path)
        return True
