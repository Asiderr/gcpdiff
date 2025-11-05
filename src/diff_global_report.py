#!/usr/bin/env python3
#
# Copyright 2025 Norbert Kamiński <norbert.kaminski@infogain.com>
#
# SPDX-License-Identifier: Apache-2.0
#

import os
import csv

from datetime import datetime
from diff_report import DiffReport


class DiffGlobalReport(DiffReport):
    def __init__(self):
        self._cmd_input = self.diff_cmdline().parse_args()
        self.tf_config_path = self._cmd_input.terraform_config
        self.api = self._cmd_input.api
        self.save_file = self._cmd_input.save_file
        self.verbose = self._cmd_input.verbose
        self.diff_log(verbose=self.verbose)

    def generate_global_report(self):
        """
        Generates a global report by comparing API schemas with Terraform
        schemas for each component, and summarizes the differences. The
        function generates individual component reports and a CSV summary
        report, containing the total number of fields, gap fields,
        eliminated gaps, and remaining gaps.

        The function performs the following steps:
        1. Loads the YAML configuration for the report.
        2. Changes the working directory to the specified Terraform
           configuration location.
        3. Retrieves API schemas.
        4. Retrieves matching Terraform resources and schemas for each API
           component.
        5. Generates component-specific reports and a global CSV summary
           report.
        6. Saves the reports in a directory named with the current date and
           time.
        """
        time_now = datetime.now()
        self.date = time_now.strftime("%Y-%m-%d_%H-%M-%S")
        csv_date = time_now.strftime("%-m/%-d/%Y")
        self.log.info("Getting YAML config")
        if not self.load_config_diff_report():
            self.log.error("Cannot get YAML config! Exiting...")
            exit(1)

        self.log.info("Changing directory to terraform config place")
        if not self.change_to_tf_dir():
            self.log.error("Cannot change workspace directory! Exiting...")
            exit(1)

        self.log.info("Getting API Schemas")
        if not self.get_api_schemas(api=self.api):
            self.log.error("Cannot get API schemas! Exiting...")
            os.chdir(self.cwd)
            exit(1)

        api_schemas_list = []
        for component in self.api_schemas:
            api_schemas_list.append(component)

        self.log.info("Getting Matching Terraform Resources")
        matching_schemas = {}
        not_matching_api = []
        if not self.get_tf_schemas():
            self.log.error("Cannot get Terraform schema! Exiting...")
            os.chdir(self.cwd)
            exit(1)

        for component in api_schemas_list:
            if component == "KeyRing":
                continue
            origin_component = component
            if "GoogleCloudApigeeV1" in component:
                component = component.split("GoogleCloudApigeeV1")[-1]
            if "GoogleCloudAiplatformV1beta1" in component:
                component = component.split("GoogleCloudAiplatformV1beta1")[-1]
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
                    self.api,
                    save_file=self.save_file
                ):
                    self.log.debug("Could not get Terraform "
                                   f"schema for {resource}")
                    continue
                tf_schemas.update({resource: self.component_tf_schema})

            if not tf_schemas:
                self.log.debug("Could not get matching Terraform resource for"
                               f" {origin_component}")
                not_matching_api.append(origin_component)
                continue
            matching_schemas.update(
                {origin_component: tf_schemas}
            )

        self.log.debug("Create directory for component reports and "
                       "csv report file")
        total_fields_number = 0
        total_api_missing = 0
        total_api_implemented = 0

        reports_dir = os.path.join(self.cwd, f"{self.date}-global-reports-"
                                   f"{self.api}-v{self.tf_provider_version}")
        csv_report = os.path.join(reports_dir,
                                  f"{self.date}-global-report-"
                                  f"{self.api}-v"
                                  f"{self.tf_provider_version}.csv")
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
        for component in matching_schemas.keys():
            self.component = component
            self.component_diff_report(directory=reports_dir)
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

        total_api_specific_fiels = (
            total_fields_number - total_api_missing - total_api_implemented
        )

        self.log.info("Number of resources analyzed:"
                      f" {len(matching_schemas)}")
        self.log.info(f"Total fields number: {total_fields_number}")
        self.log.info(f"Total api specific fields: {total_api_specific_fiels}")
        self.log.info(f"Total api implemented: {total_api_implemented}")
        self.log.info(f"Total api missing: {total_api_missing}")


if __name__ == "__main__":
    dr = DiffGlobalReport()

    dr.generate_global_report()
    exit(0)
