#!/usr/bin/env python3
from diff_common import DiffCommon, BLUE, BOLD, RED, GREEN, ENDC
from diff_api_parser import DiffApiParser
from diff_tf_parser import DiffTfParser

class DiffReport(DiffCommon, DiffApiParser,DiffTfParser):
    def __init__(self):
        self._cmd_input = self.diff_cmdline().parse_args()
        self.verbose = self._cmd_input.verbose
        self.component = self._cmd_input.component
        self.save_file = self._cmd_input.save_file
        self.diff_log(verbose=self.verbose)

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

        self.log.debug(f"{self.component} API fields: {self.api_field_list}")
        self.log.debug(f"{self.component} TF fields: {self.tf_field_list}")

        api_implemented = []
        api_missing = self.api_field_list.copy()
        tf_specific = self.tf_field_list.copy()

        for field in self.api_field_list:
            if field in self.tf_field_list:
                api_implemented.append(field)
                api_missing.remove(field)
                tf_specific.remove(field)

        self.log.info(f"{BOLD}{GREEN}API fields implemented in the "
                      f"Terraform {self.component} component{ENDC}")
        for field in api_implemented:
            self.log.info(f"{GREEN}{field}{ENDC}")

        self.log.info(f"{BOLD}{RED}API fields missing in the "
                      f"Terraform {self.component} component{ENDC}")
        for field in api_missing:
            self.log.info(f"{RED}{field}{ENDC}")

        self.log.info(f"{BOLD}{BLUE}Fields specific for "
                      f"Terraform {self.component} component{ENDC}")
        for field in tf_specific:
            self.log.info(f"{BLUE}{field}{ENDC}")

if __name__ == "__main__":
    dr = DiffReport()

    dr.generate_diff_report()
    exit(0)
