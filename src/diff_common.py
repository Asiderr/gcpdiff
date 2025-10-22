#!/usr/bin/env python3
import argparse
import logging
import os
import yaml

from diff_config import YAML_CONFIG_PATH, AWS_YAML_CONFIG_PATH, API_URLS

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

    def load_config_diff_report(self, aws=False):
        """
        Loads and parses the YAML configuration file for the diff report.
        Args:
            aws (bool): If True, load AWS-specific configuration.
                        Default is False.

        Returns:
            bool:
                - `True` if the YAML configuration is successfully loaded
                  and parsed.
                - `False` if loading or parsing the YAML configuration fails.
        """
        if aws:
            yaml_config_path = AWS_YAML_CONFIG_PATH
        else:
            yaml_config_path = YAML_CONFIG_PATH

        with open(yaml_config_path, "r") as yaml_config:
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

    def check_mapping(self, field: str):
        """
        Checks if the given field is mapped in the YAML configuration and
        returns the mapped field.

        Args:
            field (str): The field (in dot notation) to check and map.

        Returns:
            str: The fully mapped field (or original field if no mapping is
                 found).
        """
        mapped_field = ''
        split_filed = field.split(".")
        for i, subfield in enumerate(split_filed):
            try:
                mapped_part = (
                    self.yaml_config[self.component]["Mapping"][subfield]
                )
                split_filed[i] = mapped_part
            except KeyError:
                pass

        if len(split_filed) == 1:
            return split_filed[0]

        for subfield in split_filed:
            if mapped_field:
                mapped_field += f'.{subfield}'
            else:
                mapped_field = subfield
        return mapped_field

    def save_new_report(self, api_implemented, api_missing, tf_specific,
                        excluded, directory=None):
        """
        Saves the generated difference report to a YAML file.

        Args:
            api_implemented (list): List of API fields that are implemented
                                    in the Terraform component.
            api_missing (list): List of API fields that are not implemented
                                in the Terraform component.
            tf_specific (list): List of fields specific to the Terraform
                                component.
            excluded (list): List of fields explicitly excluded from the
                             comparison.

        Returns:
            bool: True if the report file is successfully saved and exists,
            False otherwise.
        """
        if not hasattr(self, 'date'):
            print("Error: Date not set!")
            return False

        self.log.info("Saving new YAML report")
        self.yaml_report = {
            "api_implemented": api_implemented,
            "api_missing": api_missing,
            "tf_specific": tf_specific,
            "excluded": excluded,
        }

        file_name = (f"{self.component}_{self.api}_diff_report_"
                     f"{self.date}-{self.tf_provider_version}.yaml")
        if directory and not os.path.exists(directory):
            return False
        elif directory:
            file_name = os.path.join(directory, file_name)
        self.log.debug(
            f"Saving {self.component} schema to json file {file_name}"
        )
        with open(file_name, "w") as f:
            yaml.dump(self.yaml_report, f)
        if not os.path.exists(file_name):
            return False
        return True
