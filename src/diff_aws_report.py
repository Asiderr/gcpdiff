#!/usr/bin/env python3
#
# Copyright 2025 Norbert Kamiński <norbert.kaminski@infogain.com>
#
# SPDX-License-Identifier: Apache-2.0
#

import csv
import os

from datetime import datetime
from diff_common import DiffCommon, BLUE, BOLD, RED, GREEN, YELLOW, CYAN, ENDC
from diff_api_parser import DiffApiParser
from diff_tf_parser import DiffTfParser


class DiffAwsReport(DiffCommon, DiffApiParser, DiffTfParser):
    def __init__(self):
        parser = self.diff_cmdline()
        parser.add_argument(
            "-p",
            "--base_api_schema_path",
            required=True,
            help="Base path to the API schemas files",
        )
        self._cmd_input = parser.parse_args()
        self.tf_config_path = self._cmd_input.terraform_config
        self.api = self._cmd_input.api
        self.base_api_schema_path = self._cmd_input.base_api_schema_path
        self.save_file = self._cmd_input.save_file
        self.verbose = self._cmd_input.verbose
        self.diff_log(verbose=self.verbose)

    def aws_component_diff_report(self, directory=None):
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
        if not self.get_aws_api_component_schema(self.component,
                                                 self.api_schema_path,
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
            if not self.get_aws_tf_component_schema(
                resource,
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
            if not self.get_tf_fields(prepend=related_resources[resource],
                                      aws=True):
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
            mapped_field = self.check_mapping(field)
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

        if not self.save_new_report(api_implemented, api_missing, tf_specific,
                                    excluded, directory=directory):
            self.log.error(f"Cannot create new diff {self.component} report! "
                           "Exiting...")
            os.chdir(self.cwd)
            exit(1)
        return True

    def generate_aws_diff_report(self):
        """
        Generates a comprehensive AWS diff report by comparing API schemas
        with Terraform schemas for multiple components.
        """
        time_now = datetime.now()
        self.date = time_now.strftime("%Y-%m-%d_%H-%M-%S")
        csv_date = time_now.strftime("%-m/%-d/%Y")
        self.log.info("Getting YAML config")
        if not self.load_config_diff_report(aws=True):
            self.log.error("Cannot get YAML config! Exiting...")
            exit(1)

        self.log.info("Changing directory to terraform config place")
        if not self.change_to_tf_dir():
            self.log.error("Cannot change workspace directory! Exiting...")
            exit(1)

        self.log.info("Getting Terraform Schemas")
        if not self.get_tf_schemas():
            self.log.error("Cannot get Terraform schemas! Exiting...")
            os.chdir(self.cwd)
            exit(1)
        tf_provider_version = (
            self.terraform_versions["provider_selections"]
                                   ["registry.terraform.io/hashicorp/aws"]
        ).replace(".", "-")

        self.log.debug("Create directory for component reports and "
                       "csv report file")
        total_fields_number = 0
        total_api_missing = 0
        total_api_implemented = 0

        reports_dir = os.path.join(self.cwd, f"{self.date}-aws-reports"
                                   f"-v{tf_provider_version}")
        csv_report = os.path.join(reports_dir,
                                  f"{self.date}-aws-report"
                                  f"-v{tf_provider_version}.csv")
        if os.path.exists(reports_dir):
            self.log.error("Global reports path exist! Check the"
                           " content of this path. Exiting...")
            exit(1)
        else:
            os.makedirs(reports_dir)

        with open(csv_report, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Provider Version", "Resource Name",
                             "Total Fields", "Gap Fields", "Eliminated Gaps",
                             "Remaining Gaps"])

        self.log.debug("Create reports each component")
        for api_schema_path, component in (
            self.yaml_config["Resources"].items()
        ):
            self.component = component
            self.api_schema_path = os.path.join(
                self.base_api_schema_path,
                f"{api_schema_path}.json"
            )
            self.aws_component_diff_report(directory=reports_dir)
            total_fields_number += self.total_fields_number
            total_api_missing += self.remaining_gaps
            total_api_implemented += self.eliminated_gaps
            with open(csv_report, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([csv_date,
                                 self.tf_provider_version,
                                 self.tf_resource_name,
                                 self.total_fields_number,
                                 self.gap_fields_number,
                                 self.eliminated_gaps,
                                 self.remaining_gaps])

        total_api_specific_fields = (
            total_fields_number - total_api_missing - total_api_implemented
        )

        self.log.info("Number of resources analyzed:"
                      f" {len(self.yaml_config['Resources'])}")
        self.log.info(f"Total fields number: {total_fields_number}")
        self.log.info("Total api specific fields: "
                      f"{total_api_specific_fields}")
        self.log.info(f"Total api implemented: {total_api_implemented}")
        self.log.info(f"Total api missing: {total_api_missing}")


if __name__ == "__main__":
    dr = DiffAwsReport()

    dr.generate_aws_diff_report()
    exit(0)
