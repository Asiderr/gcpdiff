# GCP vs Terraform Diff Report Tool

This tool compares the fields between Google Cloud API resources and their
corresponding resources in the `terraform-provider-google`
and `terraform-provider-google-beta`. It generates a detailed report showing
the differences and can optionally save the API and Terraform component schemas
as JSON files.

## Features

- **Compare GCP API fields** with the corresponding Terraform fields.
- **Compare GKE API fields** with the corresponding Terraform fields.
- **Generate a detailed diff report** of the comparison.
- Option to **save API and Terraform component schemas** as JSON files.
- **Compare the newest report with an old one** to track changes over time.

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


