#!/usr/bin/env python3

import subprocess
import diff_common
import json
import jsonref
import requests

from diff_config import DISCOVERY_DOC_URL

class DiffApiParser:
    def get_api_schemas(self):
        if not self.log:
            print("Error: Logger not found!")
            return False

        self.log.debug(
            f"Trying to dump discovery doc from: {DISCOVERY_DOC_URL}"
        )
        discovery_response = requests.get(DISCOVERY_DOC_URL)
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
            self._api_schemas = jsonref.JsonRef.replace_refs(
                ref_api_schemas,
                base_uri=DISCOVERY_DOC_URL,
                jsonschema=True
            ).get("schemas", {})
        except jsonref.JsonRefError:
            self.log.error("Dereferencing API schema has failed!")
            return False

        if not self._api_schemas:
            self.log.error("Unknown error during dereferencing API schema!")

        return True

    def get_component_schema(self, component):
        if not self.log:
            print("Error: Logger not found!")
            return False

        self.log.debug(f"Getting {component} schema")
        self.component_schema = self._api_schemas.get(component, {})
        if not self.component_schema:
            self.log.error("The specified component not found in the schema.")
            return False

        self.log.debug(self.component_schema)
        return True
