#!/usr/bin/env python3
import deepdiff
import os
import yaml

from datetime import datetime
from diff_common import DiffCommon, BLUE, BOLD, RED, GREEN, YELLOW, CYAN, ENDC
from diff_api_parser import DiffApiParser
from diff_tf_parser import DiffTfParser


class DiffReport(DiffCommon, DiffApiParser, DiffTfParser):
    def __init__(self):
        parser = self.diff_cmdline()
        parser.add_argument(
            "-c",
            "--component",
            help="Terraform component that will be compared with GCP API",
            required=True
        )
        parser.add_argument(
            "-d",
            "--diff_report",
            help=(
                "Old report file path that will be compared with the newest"
                " report"
            )
        )
        self._cmd_input = parser.parse_args()
        self.component = self._cmd_input.component
        self.tf_config_path = self._cmd_input.terraform_config
        self.api = self._cmd_input.api
        self.old_yaml_report_path = self._cmd_input.diff_report
        self.save_file = self._cmd_input.save_file
        self.verbose = self._cmd_input.verbose
        self.diff_log(verbose=self.verbose)

    def load_old_diff_report(self):
        """
        Loads and parses the old YAML diff report.

        Returns:
            bool:
                - `True` if the old YAML diff report is successfully loaded
                  and parsed.
                - `False` if there is an error with the path or loading the
                  YAML report.
        """
        if not self.old_yaml_report_path:
            self.log.error("Old YAML report path does not exist!")
            return False

        if not os.path.isabs(self.old_yaml_report_path):
            self.old_yaml_report_path = os.path.join(
                os.getcwd(),
                self.old_yaml_report_path
            )

        if not os.path.exists(self.old_yaml_report_path):
            self.log.error("Wrong old report path: "
                           f"{self.old_yaml_report_path}!")
            return False

        with open(self.old_yaml_report_path, "r") as yaml_old_report:
            self.yaml_old_report = yaml.safe_load(yaml_old_report)
        if not self.yaml_old_report:
            self.log.error("Getting old YAML report failed!")
            return False
        return True

    def _check_mapping(self, field: str):
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

    def _save_new_report(self, api_implemented, api_missing, tf_specific,
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

    def _check_new_implemented_fields(self):
        """
        Compares the current YAML report with the previous report to
        identify newly implemented API fields.

        Returns:
            bool:
                - True if the comparison completes successfully
                  (whether or not new fields were found).
                - False if the old YAML report could not be loaded.
        """
        self.log.info("Getting old YAML report")
        if not self.load_old_diff_report():
            self.log.error("Cannot get old YAML report! Exiting...")
            return False

        diff = deepdiff.DeepDiff(self.yaml_old_report, self.yaml_report)

        if diff:
            self.log.info(f"{BOLD}{GREEN}API fields implemented from the last "
                          f"report:{ENDC}")
            for _, value in diff['iterable_item_added'].items():
                self.log.info(f"{BOLD}{GREEN}{value}{ENDC}")
        else:
            self.log.info(f"{BOLD}{BLUE}No new fields implemented from the "
                          f"last report.{ENDC}")
        return True

    def component_diff_report(self, directory=None):
        """
        Generates a difference report for a specific component's API and
        Terraform schemas. The function compares the fields between the two
        schemas and logs the differences. It identifies implemented, missing,
        excluded, and specific fields for the API and Terraform, providing
        a detailed comparison report.

        Args:
        directory (str, optional): Directory to save the generated diff report.
            Defaults to None, in which case the report will be saved in
            a current directory.
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        self.log.info(f"Getting {self.component} API Schema")
        if not self.get_api_component_schema(self.component, self.api,
                                             self.save_file):
            self.log.error(
                f"Cannot get API {self.component} schema! Exiting..."
            )
            os.chdir(self.cwd)
            exit(1)

        self.log.info(f"Getting {self.component} API Schema fields")
        if not self.get_api_fields():
            self.log.error(
                f"Cannot get API {self.component} schema fields! "
                "Exiting..."
            )
            os.chdir(self.cwd)
            exit(1)

        self.log.info(f"Getting {self.component} Terraform Schema")
        related_resources = {self.component: None}
        try:
            related_resources.update(
                self.yaml_config[self.component]["RelatedResources"]
            )
        except KeyError:
            pass

        tf_schemas = {}
        main_component = None
        for resource, prepend in related_resources.items():
            if not self.get_tf_component_schema(
                resource,
                self.api,
                save_file=self.save_file
            ):
                self.log.error("Could not get Terraform "
                               f"schema for {resource}")
            tf_schemas.update({resource: self.component_tf_schema})
            if not prepend:
                main_component = self.tf_resource_name

        if main_component:
            self.tf_resource_name = main_component
        if not tf_schemas:
            self.log.error(
                f"Cannot get Terraform {self.component} schema! Exiting..."
            )
            os.chdir(self.cwd)
            exit(1)

        self.log.info(f"Getting {self.component} Terraform Schema fields")
        tf_fields = []
        for resource, schema in tf_schemas.items():
            self.component_tf_schema = schema
            if not self.get_tf_fields(prepend=related_resources[resource]):
                self.log.error(
                    f"Cannot get Terraform {resource} schema fields! "
                    "Exiting..."
                )
                os.chdir(self.cwd)
                exit(1)
            tf_fields = list(set(tf_fields + self.tf_field_list))
        self.tf_field_list = tf_fields.copy()

        self.log.debug(f"{self.component} Output Only API fields:"
                       f" {self.api_output_only}")
        self.log.debug(f"{self.component} API fields: {self.api_field_list}")
        self.log.debug(f"{self.component} TF fields: {self.tf_field_list}")

        api_implemented = []
        excluded = []
        api_missing = self.api_field_list.copy()
        tf_specific = self.tf_field_list.copy()

        self.log.debug("Substring mapping")
        for field in self.tf_field_list:
            mapped_field = self._check_mapping(field)
            if (mapped_field in self.api_field_list and
                    mapped_field not in api_implemented):
                api_implemented.append(mapped_field)
                api_missing.remove(mapped_field)
                tf_specific.remove(field)

        self.log.debug("Exact mapping")
        for field in self.api_field_list:
            try:
                mapped_field = (
                    self.yaml_config[self.component]["ExactMapping"][field]
                )
                if mapped_field in api_implemented:
                    continue
                if mapped_field in tf_specific:
                    api_missing.remove(field)
                    api_implemented.append(field)
                    tf_specific.remove(mapped_field)
            except KeyError:
                pass

        self.log.debug("Excluding fields specified in config")
        try:
            for field in self.yaml_config[self.component]["Exclude"]:
                if field in api_missing:
                    api_missing.remove(field)
                    excluded.append(field)
        except KeyError:
            pass

        self.log.debug("Excluding output only API fields")
        for field in self.api_output_only:
            if field not in excluded:
                excluded.append(field)

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

        self.total_fields_number = (len(api_implemented) + len(api_missing) +
                                    len(excluded))
        self.gap_fields_number = len(api_implemented) + len(api_missing)
        self.eliminated_gaps = len(api_implemented)
        self.remaining_gaps = len(api_missing)

        self.log.info(f"{BOLD}{BLUE}All fields per {self.component} resource:"
                      f" {self.total_fields_number}{ENDC}")
        self.log.info(f"{BOLD}{CYAN}Gap Fields:"
                      f" {self.gap_fields_number}{ENDC}")
        self.log.info(f"{BOLD}{GREEN}Eliminated Gaps:"
                      f" {self.eliminated_gaps}{ENDC}")
        self.log.info(f"{BOLD}{RED}Remaining Gaps:"
                      f" {self.remaining_gaps}{ENDC}")

        os.chdir(self.cwd)

        if not self._save_new_report(api_implemented, api_missing, tf_specific,
                                     excluded, directory=directory):
            self.log.error(f"Cannot create new diff {self.component} report! "
                           "Exiting...")
            os.chdir(self.cwd)
            exit(1)

        if (not hasattr(self, "old_yaml_report_path")
                or not self.old_yaml_report_path):
            return

        if not self._check_new_implemented_fields():
            self.log.error("Cannot compare new report with old report! "
                           "Exiting...")
            os.chdir(self.cwd)
            exit(1)

    def generate_diff_report(self):
        """
        Generates a diff report comparing the current and old API and
        Terraform field mappings.

        This method performs several tasks to generate a comprehensive diff
        report:
        1. It loads the YAML configuration for the diff report.
        2. It retrieves the API schema and fields for the specified component.
        3. It retrieves the Terraform schema and fields for the specified
           component.
        4. It compares the API and Terraform field lists, checking for
           implemented, missing, and specific fields.
        5. It excludes any fields specified in the configuration.
        6. It prints the results of the comparison in a color-coded format.
        7. It saves the newly generated diff report to a YAML file.
        8. If an old YAML report path is provided, it loads the previous diff
           report and calculates the differences using `deepdiff`.
        """
        self.date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log.info("Getting YAML config")
        if not self.load_config_diff_report():
            self.log.error("Cannot get YAML config! Exiting...")
            exit(1)

        self.log.info("Changing directory to terraform config place")
        if not self.change_to_tf_dir():
            self.log.error("Cannot change workspace directory! Exiting...")
            exit(1)

        self.log.info("Getting API Schemas")
        if not self.get_api_schemas(self.api):
            self.log.error("Cannot get API schemas! Exiting...")
            os.chdir(self.cwd)
            exit(1)

        self.log.info("Getting Terraform Schemas")
        if not self.get_tf_schemas():
            self.log.error("Cannot get Terraform schemas! Exiting...")
            os.chdir(self.cwd)
            exit(1)

        self.component_diff_report()


if __name__ == "__main__":
    dr = DiffReport()

    dr.generate_diff_report()
    exit(0)
