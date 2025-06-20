#!/usr/bin/env python3

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
}

TF_RESOURCES = {
    "compute": "google_compute_",
    "compute-beta": "google_compute_",
    "gke-std": "google_container_",
    "gke-std-beta": "google_container_",
    "gke-ent": "google_gke_hub_",
    "gke-backup": "google_gke_backup_",
    "acc-content-manager": "google_access_context_manager_",
}

YAML_CONFIG_PATH = (
    "./config.yaml"
)
