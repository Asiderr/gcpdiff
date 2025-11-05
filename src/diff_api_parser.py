#!/usr/bin/env python3
#
# Copyright 2025 Norbert Kamiński <norbert.kaminski@infogain.com>
#
# SPDX-License-Identifier: Apache-2.0
#

import json
import jsonref
import requests
import os
import time

from diff_config import API_URLS


class DiffApiParser:
    def get_api_schemas(self, api):
        """
        Retrieves and processes the API schemas from the discovery document.

        Args:
            api (str): Name of analyzed API

        Returns:
            bool:
                - `True` if the API schemas are successfully retrieved,
                  decoded, and dereferenced.
                - `False` if there is an error at any step of the process
                  (missing logger, failed JSON decoding, or dereferencing
                  issues).
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        discovery_doc_url = API_URLS[api]

        self.log.debug(
            f"Trying to get discovery doc from: {discovery_doc_url}"
        )
        discovery_response = requests.get(discovery_doc_url)
        try:
            self.log.debug("Trying to decode JSON file")
            ref_api_schemas = discovery_response.json()
        except json.decoder.JSONDecodeError:
            self.log.error("Response does not contain the JSON file!")
            return False

        if not ref_api_schemas:
            self.log.error("Unknown error during parsing discovery doc!")
            return False

        try:
            self.log.debug("Trying to dereference API schemas")
            self.api_schemas = jsonref.JsonRef.replace_refs(
                ref_api_schemas,
                base_uri=discovery_doc_url,
                jsonschema=True
            ).get("schemas", {})
        except jsonref.JsonRefError:
            self.log.error("Dereferencing API schema has failed!")
            return False

        if not self.api_schemas:
            self.log.error("Unknown error during dereferencing API schema!")
            return False

        return True

    def get_aws_api_component_schema(self, component, schema_path,
                                     save_file=False):
        """
        Retrieves and processes the AWS API schemas from the provided
        json file.

        Args:
            api_schemas (str): Path to AWS API schemas json file.

        Returns:
            bool:
                - `True` if the API schemas are successfully set.
                - `False` if there is an error at any step of the process
                  (missing logger or empty API schemas).
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        if not os.path.exists(schema_path):
            self.log.error(f"AWS schema path {schema_path} does not exist!")
            return False

        with open(schema_path, "r") as f:
            self.log.debug("Loading AWS API schemas from json file:"
                           f" {schema_path}")
            ref_component_api_schema = json.load(f)

        self.component_api_schema = jsonref.JsonRef.replace_refs(
                ref_component_api_schema,
                jsonschema=True
            )

        if not self.component_api_schema:
            self.log.error(f"{component} API schema is empty!")
            return False

        if save_file:
            file_name = os.path.join(
                self.cwd,
                (f"{component}_aws_api_{round(time.time())}.json")
            )
            self.log.debug(
                f"Saving {component} schema to json file {file_name}"
            )
            with open(file_name, "w") as f:
                json.dump(self.component_api_schema, f, indent=2)
        return True

    def get_azure_api_component_schema(self, component, repo_schema_path,
                                       save_file=False):
        """
        Retrieves and processes component azure API schemas from the provided
        path.

        Args:
            repo_schema_path (str): Path to Azure API schemas repo.
            component (str): The name of the component for which the API schema
                             is to be retrieved.
            save_file (bool, optional): If `True`, the schema is saved to
                                        a JSON file. Defaults to `False`.
        Returns:
            bool:
                - `True` if the API schemas are successfully set.
                - `False` if there is an error at any step of the process
                  (missing logger or empty API schemas).
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        schema_path = os.path.join(repo_schema_path,
                                   f"{API_URLS[self.api]}.json")

        if not os.path.exists(schema_path):
            self.log.error(f"Azure schema path {schema_path} does not exist!")
            return False

        with open(schema_path, "r") as f:
            self.log.debug("Loading Azure API schemas from json file:"
                           f" {schema_path}")
            ref_component_api_schema = json.load(f)

        api_schema = jsonref.JsonRef.replace_refs(
                ref_component_api_schema,
                jsonschema=True
            )
        try:
            self.component_api_schema = (
                api_schema["resourceDefinitions"][component]
            )
        except KeyError:
            self.log.error(f"Resource definitions for {component} not found!")
            return False

        if not self.component_api_schema:
            self.log.error(f"{component} API schema is empty!")
            return False

        if save_file:
            file_name = os.path.join(
                self.cwd,
                (f"{component}_azure_api_{round(time.time())}.json")
            )
            self.log.debug(
                f"Saving {component} schema to json file {file_name}"
            )
            with open(file_name, "w") as f:
                json.dump(self.component_api_schema, f, indent=2)
        return True

    def get_api_component_schema(self, component, api, save_file=False):
        """
        Retrieves the API schema for a specified component and optionally
        saves it to a file.

        Args:
            component (str): The name of the component for which the API schema
                             is to be retrieved.
            api (str): Name of analyzed API
            save_file (bool, optional): If `True`, the schema is saved to
                                        a JSON file. Defaults to `False`.

        Returns:
            bool:
                - `True` if the API schema is successfully retrieved and
                  optionally saved to a file.
                - `False` if any required attributes are missing, or the
                  component schema cannot be found.
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        if not hasattr(self, 'cwd'):
            self.log.error("Error: Current directory not set!")
            return False

        if not hasattr(self, 'api_schemas'):
            self.log.error("Error: API schemas not set!")
            return False

        self.log.debug(f"Getting {component} schema")
        self.component_api_schema = self.api_schemas.get(component)
        if not self.component_api_schema:
            self.log.error("The specified component not found in the schema!")
            return False

        if save_file:
            file_name = os.path.join(
                self.cwd,
                (f"{component}_{api}_api_{round(time.time())}.json")
            )
            self.log.debug(
                f"Saving {component} schema to json file {file_name}"
            )
            with open(file_name, "w") as f:
                json.dump(self.component_api_schema, f, indent=2)
        return True

    def _get_api_field(self, key_origin, value_origin):
        """
        Recursively extracts API field keys from a given schema and appends
        them to `self.api_field_list`.

        Args:
            key_origin (str): The key path of the current field being processed
                              (used for nested fields).
            value_origin (dict): The current level of the schema to process,
                                 typically a dictionary containing
                                 "properties" or "items" keys with their
                                 respective values.
        """
        nested = False
        key_appendix = ''
        if key_origin != '':
            key_appendix = key_origin + '.'

        try:
            for key, value in value_origin["properties"].items():
                if key != "properties":
                    self._get_api_field(key_appendix+key, value)
                else:
                    self._get_api_field(key_appendix, value)
            nested = True
        except KeyError:
            pass

        try:
            for key, value in value_origin["items"]["properties"].items():
                self._get_api_field(key_appendix+key, value)
            nested = True
        except KeyError:
            pass

        if not nested and key_origin not in self.api_field_list:
            try:
                if "[Output Only]" in value_origin["description"]:
                    self.api_output_only.append(key_origin)
                elif "Output only." in value_origin["description"]:
                    self.api_output_only.append(key_origin)
                else:
                    self.api_field_list.append(key_origin)
            except KeyError:
                self.api_field_list.append(key_origin)

    def _get_azure_api_field(self, key_origin, value_origin):
        """
        Recursively extracts azure API field keys from a given schema and
        appends them to `self.api_field_list`.

        Args:
            key_origin (str): The key path of the current field being processed
                              (used for nested fields).
            value_origin (dict): The current level of the schema to process,
                                 typically a dictionary containing
                                 "properties" or "items" keys with their
                                 respective values.
        """
        nested = False
        key_appendix = ''
        if not value_origin:
            return
        if key_origin != '':
            key_appendix = key_origin + '.'

        try:
            for key, value in value_origin["properties"].items():
                if key != "properties":
                    self._get_azure_api_field(key_appendix+key, value)
                else:
                    self._get_azure_api_field(key_appendix, value)
            nested = True
        except KeyError:
            pass

        try:
            for key, value in value_origin["oneOf"][0]["properties"].items():
                if key != "properties":
                    self._get_azure_api_field(key_appendix+key, value)
                else:
                    self._get_azure_api_field(key_appendix, value)
            nested = True
        except KeyError:
            pass

        try:
            for key, value in (
                value_origin["items"]["oneOf"][0]["properties"].items()
            ):
                self._get_azure_api_field(key_appendix+key, value)
            nested = True
        except KeyError:
            pass

        if not nested and key_origin not in self.api_field_list:
            try:
                if "[Output Only]" in value_origin["description"]:
                    self.api_output_only.append(key_origin)
                elif "Output only." in value_origin["description"]:
                    self.api_output_only.append(key_origin)
                else:
                    self.api_field_list.append(key_origin)
            except KeyError:
                self.api_field_list.append(key_origin)

    def get_api_fields(self, azure=False):
        """
        Retrieves the API fields from the component API schema.

        Args:
            azure (bool): If True, process the schema as an Azure API schema.

        Returns:
            bool:
                - `True` if the API fields are successfully retrieved and
                  `self.api_field_list` is populated.
                - `False` if an error occurs (e.g., missing attributes or
                  empty field list).
        """
        if not hasattr(self, 'log'):
            print("Error: Logger not found!")
            return False

        if not hasattr(self, 'component_api_schema'):
            self.log.error("API component schema not found!")
            return False

        self.api_field_list = []
        self.api_output_only = []
        if azure:
            self._get_azure_api_field('', self.component_api_schema)
        else:
            self._get_api_field('', self.component_api_schema)

        if not self.api_field_list:
            self.log.error("Failed to get API component fields!")
            return False

        return True
