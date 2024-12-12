#!/usr/bin/env python3
import yaml

from diff_common import DiffCommon, BLUE, BOLD, RED, GREEN, YELLOW, ENDC
from diff_api_parser import DiffApiParser
from diff_tf_parser import DiffTfParser
from diff_config import YAML_CONFIG_PATH

class DiffReport(DiffCommon, DiffApiParser,DiffTfParser):
    def __init__(self):
        self._cmd_input = self.diff_cmdline().parse_args()
        self.verbose = self._cmd_input.verbose
        self.component = self._cmd_input.component
        self.save_file = self._cmd_input.save_file
        self.diff_log(verbose=self.verbose)

    def load_config_diff_report(self):
        with open(YAML_CONFIG_PATH, "r") as yaml_config:
            self.yaml_config = yaml.safe_load(yaml_config)
        if not self.yaml_config:
            self.log.error("Getting YAML config failed!")
            return False
        return True

    def check_mapping(self, field:str):
        nested = True
        mapped_field = ''
        split_filed = field.split(".")
        for i ,subfield in enumerate(split_filed):
            try:
                mapped_part = (
                    self.yaml_config[self.component]["Mapping"][subfield]
                )
                split_filed[i] = mapped_part
            except KeyError:
                pass

        if len(split_filed) == 0:
            return split_filed[0]


        for subfield in split_filed:
            if mapped_field:
                mapped_field += f'.{subfield}'
            else:
                mapped_field = subfield
        return mapped_field

    def generate_diff_report(self):
        """
        """
        self.log.info(f"Getting {self.component} API Schema")
        if not self.get_api_component_schema(self.component, self.save_file):
            self.log.error(
                f"Cannot get API {self.component} schema! Exiting..."
            )
            exit(1)

        self.log.info(f"Getting {self.component} API Schema fields")
        if not self.get_api_fields():
            self.log.error(
                f"Cannot get API {self.component} schema fields! "
                "Exiting..."
            )
            exit(1)

        self.log.info(f"Getting {self.component} Terraform Schema")
        if not self.get_tf_component_schema(self.component, self.save_file):
            self.log.error(
                f"Cannot get Terraform {self.component} schema! Exiting..."
            )
            exit(1)

        self.log.info(f"Getting {self.component} Terraform Schema fields")
        if not self.get_tf_fields():
            self.log.error(
                f"Cannot get Terraform {self.component} schema fields! "
                "Exiting..."
            )
            exit(1)

        self.log.info(f"Getting YAML config")
        if not self.load_config_diff_report():
            self.log.error(f"Cannot get YAML config! Exiting...")
            exit(1)


        self.log.debug(f"{self.component} API fields: {self.api_field_list}")
        self.log.debug(f"{self.component} TF fields: {self.tf_field_list}")

        api_implemented = []
        excluded = []
        api_missing = self.api_field_list.copy()
        tf_specific = self.tf_field_list.copy()

        for field in self.tf_field_list:
            mapped_field = self.check_mapping(field)
            if mapped_field in self.api_field_list and mapped_field not in api_implemented:
                api_implemented.append(mapped_field)
                api_missing.remove(mapped_field)
                tf_specific.remove(field)

        try:
            for field in self.yaml_config[self.component]["Exclude"]:
                if field in api_missing:
                    api_missing.remove(field)
                    excluded.append(field)
        except KeyError:
            pass

        self.log.info(f"{BOLD}{GREEN}API fields implemented in the "
                      f"Terraform {self.component} component{ENDC}")
        for field in api_implemented:
            self.log.info(f"{GREEN}{field}{ENDC}")

        self.log.info(f"{BOLD}{RED}API fields missing in the "
                      f"Terraform {self.component} component{ENDC}")
        for field in api_missing:
            self.log.info(f"{RED}{field}{ENDC}")

        self.log.info(f"{BOLD}{YELLOW}Fields excluded form comparison:{ENDC}")
        for field in excluded:
            self.log.info(f"{YELLOW}{field}{ENDC}")

        self.log.info(f"{BOLD}{BLUE}Fields specific for "
                      f"Terraform {self.component} component{ENDC}")
        for field in tf_specific:
            self.log.info(f"{BLUE}{field}{ENDC}")

if __name__ == "__main__":
    dr = DiffReport()

    dr.generate_diff_report()
    exit(0)
