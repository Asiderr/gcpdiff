#!/usr/bin/env python3
#
# Copyright 2025 Norbert Kamiński <norbert.kaminski@infogain.com>
#
# SPDX-License-Identifier: Apache-2.0
#

API_URLS = {
    "compute": "https://www.googleapis.com/discovery/v1/apis/compute/v1/rest",
    "compute-beta": (
        "https://www.googleapis.com/discovery/v1/apis/compute/beta/rest"
    ),
    "gke-std": "https://container.googleapis.com/$discovery/rest?version=v1",
    "gke-std-beta": (
        "https://container.googleapis.com/$discovery/rest?version=v1"
    ),
    "gke-ent": "https://gkehub.googleapis.com/$discovery/rest?version=v1",
    "gke-backup": (
        "https://gkebackup.googleapis.com/$discovery/rest?version=v1"
    ),
    "acc-content-manager": (
        "https://accesscontextmanager.googleapis.com/$discovery/"
        "rest?version=v1"
    ),
    "storage-beta": (
        "https://storage.googleapis.com/$discovery/rest?version=v1"
    ),
    "apigee-beta": (
        "https://apigee.googleapis.com/$discovery/rest?version=v1"
    ),
    "networksecurity-beta": (
        "https://networksecurity.googleapis.com/$discovery/rest?version=v1"
    ),
    "vertexai-beta": (
        "https://aiplatform.googleapis.com/$discovery/rest?version=v1beta1"
    ),
    "networkservices-beta": (
        "https://networkservices.googleapis.com/$discovery"
        "/rest?version=v1beta1"
    ),
    "logging-beta": (
        "https://logging.googleapis.com/$discovery/rest?version=v2"
    ),
    "kms-beta": (
        "https://cloudkms.googleapis.com/$discovery/rest?version=v1"
    ),
    "monitoring-beta": (
        "https://monitoring.googleapis.com/$discovery/rest?version=v3"
    ),
    "azurerm-compute": "Microsoft.Compute",
}

TF_RESOURCES = {
    "compute": "google_compute_",
    "compute-beta": "google_compute_",
    "gke-std": "google_container_",
    "gke-std-beta": "google_container_",
    "gke-ent": "google_gke_hub_",
    "gke-backup": "google_gke_backup_",
    "acc-content-manager": "google_access_context_manager_",
    "storage-beta": "google_storage_",
    "apigee-beta": "google_apigee_",
    "networksecurity-beta": "google_network_security_",
    "vertexai-beta": "google_vertex_ai_",
    "networkservices-beta": "google_network_services_",
    "logging-beta": "google_logging_",
    "kms-beta": "google_kms_",
    "monitoring-beta": "google_monitoring_"
}

YAML_CONFIG_PATH = "./config.yaml"
AWS_YAML_CONFIG_PATH = "./aws_config.yaml"
AZURE_YAML_CONFIG_PATH = "./azure_config.yaml"
