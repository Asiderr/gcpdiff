#!/usr/bin/env python3
#
# Copyright 2025 Norbert Kamiński <norbert.kaminski@infogain.com>
#
# SPDX-License-Identifier: Apache-2.0
#

import deepdiff
import os
import yaml

from datetime import datetime
from diff_report import DiffReport


class DiffApiCompare(DiffReport):
    """
    Class for comparing API schemas between different versions.
    """
    def __init__(self):
        parser = self.diff_cmdline()
        parser.add_argument(
            "-d",
            "--diff_report",
            help=(
                "Old report file path that will be compared with the newest"
                " report"
            )
        )
        self._cmd_input = parser.parse_args()
        self.tf_config_path = self._cmd_input.terraform_config
        self.save_file = self._cmd_input.save_file
        self.verbose = self._cmd_input.verbose
        self.old_yaml_report_path = self._cmd_input.diff_report
        self.diff_log(verbose=self.verbose)

    def generate_api_comparison(self):
        """
        Method to generate comparison report between V1 and beta API schemas.
        """
        time_now = datetime.now()
        self.date = time_now.strftime("%Y-%m-%d_%H-%M-%S")
        self.log.info("Getting YAML config")
        if not self.load_config_diff_report():
            self.log.error("Cannot get YAML config! Exiting...")
            exit(1)

        self.log.info("Changing directory to terraform config place")
        if not self.change_to_tf_dir():
            self.log.error("Cannot change workspace directory! Exiting...")
            exit(1)

        self.log.info("Getting V1 API Schemas")
        if not self.get_api_schemas(api="compute"):
            self.log.error("Cannot get V1 API schemas! Exiting...")
            os.chdir(self.cwd)
            exit(1)

        v1_api_schemas_list = []
        v1_api_schemas = self.api_schemas.copy()
        for component in self.api_schemas:
            v1_api_schemas_list.append(component)

        self.log.info("Getting beta API Schemas")
        if not self.get_api_schemas(api="compute-beta"):
            self.log.error("Cannot get Beta API schemas! Exiting...")
            os.chdir(self.cwd)
            exit(1)

        beta_api_schemas_list = []
        beta_api_schemas = self.api_schemas.copy()
        for component in self.api_schemas:
            beta_api_schemas_list.append(component)

        self.log.info("Getting Terraform Schemas")
        if not self.get_tf_schemas():
            self.log.error("Cannot get Terraform schema! Exiting...")
            os.chdir(self.cwd)
            exit(1)

        self.log.info("Getting Matching V1 Terraform Resources")
        matching_schemas_v1 = {}
        not_matching_api_v1 = []

        for component in v1_api_schemas_list:
            self.log.debug(f"Trying to match {component} with Terraform"
                           " resource")
            related_resources = {component: None}
            try:
                related_resources.update(
                    self.yaml_config[component]["RelatedResources"]
                )
            except KeyError:
                pass

            tf_schemas = {}
            for resource, _ in related_resources.items():
                if not self.get_tf_component_schema(
                    resource,
                    "compute",
                    save_file=self.save_file
                ):
                    self.log.debug("Could not get Terraform "
                                   f"schema for {resource}")
                    continue
                tf_schemas.update({resource: self.component_tf_schema})

            if not tf_schemas:
                self.log.debug("Could not get matching Terraform resource for"
                               f" {component}")
                not_matching_api_v1.append(component)
                continue
            matching_schemas_v1.update(
                {component: tf_schemas}
            )

        report_dir = os.path.join(self.cwd, f"{self.date}-compare-"
                                  f"apis-v{self.tf_provider_version}.yaml")
        if os.path.exists(report_dir):
            self.log.error("Compare report file exist! Check the"
                           f" content of this path: {report_dir}. Exiting...")
            exit(1)

        self.log.info("Creating API schemas comparison for components")
        for component in matching_schemas_v1.keys():
            if not self.compare_api_fields(component, v1_api_schemas,
                                           beta_api_schemas,
                                           report_dir=report_dir):
                self.log.error(f"Cannot compare {component} v1 and beta"
                               " schemas!")
                continue

        if not os.path.exists(report_dir):
            self.log.error("Creation of the comparison report failed!"
                           " Exiting...")
            exit(1)

        self.log.info("Comparison report created successfully! Check file:"
                      f" {report_dir}")
        os.chdir(self.cwd)

        if (not hasattr(self, "old_yaml_report_path")
                or not self.old_yaml_report_path):
            return

        if not self._check_new_api_differences(report_dir):
            self.log.error("Cannot compare new report with old report! "
                           "Exiting...")
            os.chdir(self.cwd)
            exit(1)

        compare_dir = os.path.join(self.cwd, f"{self.date}-reports-comparison"
                                   f"-v{self.tf_provider_version}.yaml")

        if os.path.exists(compare_dir):
            self.log.error("Report comparison file exist! Check the"
                           f" content of this path: {compare_dir}. Exiting...")
            exit(1)

        with open(compare_dir, "w") as f:
            yaml.dump(self.result, f)

    def compare_api_fields(self, component, v1_schemas, beta_schemas,
                           report_dir=None):
        """
        Compares API fields between V1 and beta schemas for a specified
        component and generates a report of fields that are only present
        in the beta schema.
        Args:
            component (str): The name of the component to compare.
            v1_schemas (dict): A dictionary containing V1 API schemas.
            beta_schemas (dict): A dictionary containing beta API schemas.
            report_dir (str): The directory path to save the comparison report.
        Returns:
            bool: True if the comparison is successful and the report is
                   created, False otherwise.
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        self.log.debug(f"Getting v1 api schema for {component}")
        component_v1_schema = v1_schemas.get(component)
        if not component_v1_schema:
            self.log.error("The specified component not found in the schema!")
            return False

        self.log.debug(f"Getting beta api schema for {component}")
        component_beta_schema = beta_schemas.get(component)
        if not component_beta_schema:
            self.log.error("The specified component not found in the schema!")
            return False

        self.log.debug(f"Getting api fields for {component} v1")
        self.component_api_schema = component_v1_schema
        if not self.get_api_fields():
            self.log.error(f"Cannot get API fields for {component} v1!")
            return False
        component_v1_fields = self.api_field_list.copy()

        self.log.debug(f"Getting api fields for {component} beta")
        self.component_api_schema = component_beta_schema
        if not self.get_api_fields():
            self.log.error(f"Cannot get API fields for {component} beta!")
            return False
        component_beta_fields = self.api_field_list.copy()

        self.log.debug(f"Fields only in beta API {component} schema")
        beta_only_fields = [
            field for field in component_beta_fields
            if field not in component_v1_fields
        ]

        with open(report_dir, "a") as f:
            yaml.dump({component: beta_only_fields}, f)
        if not os.path.exists(report_dir):
            return False
        return True

    def _check_new_api_differences(self, report_dir):
        """
        Compares the newly generated API comparison report with an old report
        and identifies differences between them.
        Args:
            report_dir (str): The directory path of the new comparison report.
        Returns:
            bool: True if the comparison is successful, False otherwise.
        """
        self.log.info("Getting old YAML report")
        if not self.load_old_diff_report():
            self.log.error("Cannot get old YAML report! Exiting...")
            return False

        with open(report_dir, "r") as yaml_report:
            diff = deepdiff.DeepDiff(yaml.safe_load(yaml_report),
                                     self.yaml_old_report)
        self.result = {"Added to beta API": {}, "Implemented in V1 API": {}}
        for action, values in diff.items():
            if action == "iterable_item_added":
                key = "Added to beta API"
            elif action == "iterable_item_removed":
                key = "Implemented in V1 API"
            else:
                self.log.error(f"Unknown action {action} found!")
                return False
            for resource, value in values.items():
                resource_formatted = resource.split("root['")[1].split("']")[0]
                try:
                    resource_values = self.result[key][resource_formatted]
                    resource_values.append(value)
                    self.result[key].update(
                        {resource_formatted: resource_values}
                    )
                except KeyError:
                    self.result[key].update({resource_formatted: [value]})

        return True


if __name__ == "__main__":
    dr = DiffApiCompare()

    dr.generate_api_comparison()
    exit(0)
