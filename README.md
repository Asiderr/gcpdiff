# GCP vs Terraform Diff Report Tool

This tool compares the fields between Google Cloud API resources and their
corresponding resources in the `terraform-provider-google`
and `terraform-provider-google-beta`. It generates a detailed report showing
the differences and can optionally save the API and Terraform component schemas
as JSON files.

## Quick start

1. Download diff tool

```bash
git clone https://github.com/Asiderr/gcpdiff.git
```

2. Intall pip requirements

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r gcpdiff/requirements.txt
```

3. Create main.tf
```t
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
    google-beta = {
      source = "hashicorp/google-beta"
    }
  }
}
```

4. Run initialize terraform
```bash
terraform init
```

5. Generate reports for GCP compute-beta
```bash
gcpdiff/src/diff_global_report.py -t . -a compute-beta
```

## Features

- **Compare GCP API fields** with the corresponding Terraform fields.
- **Compare GKE API fields** with the corresponding Terraform fields.
- **Generate a detailed diff report** of the comparison.
- Option to **save API and Terraform component schemas** as JSON files.
- **Compare the newest report with an old one** to track changes over time.
- **Compare V1 and beta terraform fields**.
- **Compare AWS EC2 API fields** with the corresponding Terraform fields.
- **Compare Azure RM API fields** with the corresponding Terraform fields.

## Installation

1. Clone the repository:
    ```bash
    git clone git@github.com:Asiderr/gcpdiff.git
    ```

2. Install the necessary dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Ensure you have `terraform` installed and properly configured on your system.

## Usage

### Diff report for single terraform component

To use the tool, run the following command:

```bash
gcpdiff/src/diff_report.py -h
```

#### Required arguments

* `-t TERRAFORM_CONFIG`, `--terraform_config` TERRAFORM_CONFIG
                        Path to the terraform config main.tf file
* `-c COMPONENT`, `--component COMPONENT`: The Terraform component that will be
                                          compared with the GCP API (e.g., Instance).
* `-a {compute,compute-beta,gke-std,gke-std-beta,gke-ent,gke-backup}`,
  `--api {compute,compute-beta,gke-std,gke-std-beta,gke-ent,gke-backup}`:
                                          The Google API that will be analyzed
#### Optional arguments

* `-d DIFF_REPORT`, `--diff_report DIFF_REPORT`: Path to the old report file that
                                                 will be compared with the newest
                                                 report.
* `-s, --save_file`: Save the API and Terraform component schemas as JSON files.
* `-v, --verbose`: Increase the log verbosity level.
* `-h, --help`: Show the help message and exit.

#### Examples

Create simple report for google_compute_instance:

```bash
gcpdiff/src/diff_report.py -c Instance -t /path/to/terraform/config
```

Create simple report for google_compute_instance and save schemas as JSON files
and compare with an old report:

```bash
gcpdiff/src/diff_report.py -v -c Instance -t /path/to/terraform/config -s -d /path/to/old_report.yaml
```

### Global diff report

To use the tool, run the following command:

```bash
gcpdiff/src/diff_report.py -h
```

#### Required arguments

* `-t TERRAFORM_CONFIG`, `--terraform_config` TERRAFORM_CONFIG
                        Path to the terraform config main.tf file
* `-a {compute,compute-beta,gke-std,gke-std-beta,gke-ent,gke-backup}`,
  `--api {compute,compute-beta,gke-std,gke-std-beta,gke-ent,gke-backup}`:
                                          The Google API that will be analyzed

#### Optional arguments

* `-s, --save_file`: Save the API and Terraform component schemas as JSON files.
* `-v, --verbose`: Increase the log verbosity level.
* `-h, --help`: Show the help message and exit.

#### Examples

Create global report for Compute API:

```bash
gcpdiff/src/diff_global_report.py -t /path/to/terraform/config
```

Create global report for Compute beta API:

```bash
gcpdiff/src/diff_global_report.py -t /path/to/terraform/config -a compute-beta
```

Create global report for GKE Enterprise API:

```bash
gcpdiff/src/diff_global_report.py -t /path/to/terraform/config -a gke-ent
```

### V1 and beta GCP compute API comparison report

Compares V1 and Beta GCP Compute terraform fields.

To use the tool, run the following command:

```bash
gcpdiff/src/diff_api_compare.py -h
```

#### Required arguments

* `-t TERRAFORM_CONFIG`, `--terraform_config` TERRAFORM_CONFIG
                        Path to the terraform config main.tf file
* `-a {compute,compute-beta,gke-std,gke-std-beta,gke-ent,gke-backup}`,
  `--api {compute,compute-beta,gke-std,gke-std-beta,gke-ent,gke-backup}`:
                                          The Google API that will be analyzed

> For now this tool works only for GCP compute API

#### Optional arguments

* `-s, --save_file`: Save the API and Terraform component schemas as JSON files.
* `-v, --verbose`: Increase the log verbosity level.
* `-h, --help`: Show the help message and exit.

#### Examples

Create comparison between V1 and beta for GCP Compute API:

```bash
gcpdiff/src/diff_api_compare.py -t /path/to/terraform/config -a compute-beta
```

### Global diff report for AWS

To use the tool, run the following command:

```bash
gcpdiff/src/diff_aws_report.py -h
```

#### Required arguments

* `-t TERRAFORM_CONFIG`, `--terraform_config` TERRAFORM_CONFIG
    Path to the terraform config main.tf file
* `-p BASE_API_SCHEMA_PATH`, `--base_api_schema_path BASE_API_SCHEMA_PATH`
    Base path to the API schemas files

#### Optional arguments

* `-s, --save_file`: Save the API and Terraform component schemas as JSON files.
* `-v, --verbose`: Increase the log verbosity level.
* `-h, --help`: Show the help message and exit.

#### Examples

```bash
gcpdiff/src/diff_aws_report.py -t /path/to/terraform/config -p /path/to/aws/api/schemas
```

### Global diff report for Azure Resource Manager

To use the tool, run the following command:

```bash
gcpdiff/src/diff_azure_report.py -h
```

#### Required arguments

* `-t TERRAFORM_CONFIG`, `--terraform_config` TERRAFORM_CONFIG
    Path to the terraform config main.tf file
* `-a {compute,compute-beta,gke-std,gke-std-beta,gke-ent,gke-backup}`,
  `--api {compute,compute-beta,gke-std,gke-std-beta,gke-ent,gke-backup}`:
                                          The Google API that will be analyzed
* `-p BASE_API_SCHEMA_PATH`, `--base_api_schema_path BASE_API_SCHEMA_PATH`
    Base path to the API schemas files

#### Optional arguments

* `-s, --save_file`: Save the API and Terraform component schemas as JSON files.
* `-v, --verbose`: Increase the log verbosity level.
* `-h, --help`: Show the help message and exit.

#### Examples

```bash
gcpdiff/src/diff_azure_report.py -t /path/to/terraform/config -a azurerm-compute -p /path/to/azure/api/schemas
```
