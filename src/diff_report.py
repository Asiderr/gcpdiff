#!/usr/bin/env python3
from diff_common import DiffCommon
from diff_api_parser import DiffApiParser

class DiffReport(DiffCommon, DiffApiParser):
    def __init__(self):
        self._cmd_input = self.diff_cmdline().parse_args()
        self.verbose = self._cmd_input.verbose
        self.component = self._cmd_input.component
        self.diff_log(verbose=self.verbose)

    def generate_diff_report(self):
        if not self.get_api_schemas():
            self.log.error("Cannot get GCP API schemas! Exiting...")
            exit(1)

        if not self.get_component_schema(self.component):
            self.log.error(f"Cannot get {self.component} schema! Exiting...")
            exit(1)


if __name__ == "__main__":
    dr = DiffReport()

    dr.generate_diff_report()
    exit(0)
