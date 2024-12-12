#!/usr/bin/env python3

import json
import re
import subprocess
import time

class DiffTfParser:
    def terraform_check(self):
        """
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        cmd_version = ["terraform", "--version"]
        self.log.debug("CMD: " + " ".join(cmd_version))

        try:
            p = subprocess.Popen(cmd_version, stdout=subprocess.PIPE)
            p.wait()
            if p.returncode != 0:
                self.log.error(f"Terraform version check failed!")
                return False
        except FileNotFoundError:
            self.log.error(f"Terraform command not available!")
            return False
        return True

    def get_tf_schemas(self):
        """
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        self.log.debug("Checking if Terraform is available")
        if not self.terraform_check():
            return False

        self.log.debug("Trying to get Terraform schemas")
        cmd_get_schemas = ["terraform", "providers", "schema", "-json"]
        p = subprocess.Popen(
            cmd_get_schemas,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, __ = p.communicate()
        terraform_stdout = stdout.decode("utf-8")

        if p.returncode != 0:
            self.log.error("Getting Terraform schemas failed!")
            return False

        if terraform_stdout == '{"format_version":"1.0"}\n':
            self.log.error(
                "No info about Terraform schemas! "
                "Check if Terraform configuration is available."
            )
            return False

        self.terraform_schemas = json.loads(terraform_stdout)

        return True

    def camel_to_snake_string(self, camel):
        """
        Method converts camel string into snake case

        Args:
            camel (str): String that needs to be converted

        Returns:
            Snake case string
        """
        return re.sub(r'(?<!^)(?=[A-Z])', '_', camel).lower()

    def snake_to_camel_string(self, snake):
        """
        """
        parts = snake.split('_')
        return parts[0] + ''.join(word.capitalize() for word in parts[1:])

    def snake_to_camel_schema(self, schema):
        if isinstance(schema, dict):
            return {
                self.snake_to_camel_string(key):
                self.snake_to_camel_schema(value)
                for key, value in schema.items()
            }
        elif isinstance(schema, list):
            return [self.snake_to_camel_schema(item) for item in schema]
        else:
            return schema

    def get_tf_component_schema(self, component, save_file=False):
        """
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        if not self.get_tf_schemas():
            self.log.error("Cannot get Terraform schemas!")
            return False

        try:
            self.component_tf_schema = self.snake_to_camel_schema(
                self.terraform_schemas[
                    "provider_schemas"][
                    "registry.terraform.io/hashicorp/google"][
                    "resource_schemas"][
                    f"google_compute_{self.camel_to_snake_string(component)}"]
            )
        except KeyError:
            self.log.error("The specified component not found in the schema.")
            return False

        if save_file:
            file_name = f"{component}_terraform_schema_{time.time()}.json"
            self.log.debug(
                f"Saving {component} schema to json file {file_name}"
            )
            with open(file_name, "w") as f:
                json.dump(self.component_tf_schema, f, indent=2)
        return True

    def get_nested_attributes(self, key, type_list:list):
        nested = False

        for type in type_list:
            if isinstance(type, list):
                nested = True
                for subkey in type[1].keys():
                    self.tf_field_list.append(key + "." + subkey)
                continue

        if not nested:
            self.tf_field_list.append(key)


    def get_tf_field(self, key_origin, value_origin):
        """
        """
        key_appendix = ''
        if key_origin != '':
            key_appendix = key_origin + '.'

        try:
            for key, value in value_origin["block"]["attributes"].items():
                if not isinstance(value["type"], list):
                    self.tf_field_list.append(key_appendix+key)
                    continue
                self.get_nested_attributes(key_appendix+key, value["type"])
        except KeyError:
            pass

        try:
            for key,value in value_origin["block"]["blockTypes"].items():
                self.get_tf_field(key_appendix+key, value)
        except KeyError:
            pass

    def get_tf_fields(self):
        """
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        if not hasattr(self, 'component_tf_schema'):
            self.log.error("Terraform component schema not found!")
            return False

        self.tf_field_list = []
        self.get_tf_field('', self.component_tf_schema)

        if not self.tf_field_list:
            self.log.error("Failed to get Terraform component fields!")
            return False

        return True
