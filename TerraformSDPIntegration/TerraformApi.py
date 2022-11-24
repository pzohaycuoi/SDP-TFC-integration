import requests
from os.path import exists


def workspace_create(token: str, terraform_org: str, workspace_name: str, auto_apply=False):
    """
    Create Terraform workspace
    Construct API request and send API request for Terraform workspace creation.
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces
    :param terraform_org: Terraform organization name
    :param token: Terraform user token has enough permission to create workspace
    :param workspace_name: Terraform workspace name
    :param auto_apply: Terraform workspace auto-apply setting, if set to True,Terraform will run apply
    after success Terraform run plan.
    :return: API response
    """
    payload = {"data": {"attributes": {"name": workspace_name, "description": "Created by API call",
                                       "auto_apply": auto_apply}, "type": "workspaces"}}
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/organizations/{terraform_org}/workspaces?"
    try:
        req = requests.post(url, json=payload, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def workspace_get(token: str, terraform_org: str, workspace_name: str):
    """
    Get Terraform workspace information through API request
    Construct API request and send API request for getting the workspace information
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces
    :param terraform_org: Terraform organization name
    :param token: Terraform user token
    :param workspace_name: Terraform workspace name
    :return: API response
    """
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/organizations/{terraform_org}/workspaces/{workspace_name}"
    try:
        req = requests.post(url, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def workspace_config_create(token: str, workspace_id: str, auto_queue=False):
    """
    Create Terraform workspace configuration version for Terraform workspace doesn't attach to any VCS (Git/Gitlab repo)
    Construct API request and send API request for creation of Terraform workspace configuration versions
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/configuration-versions#create-a-configuration-version
    :param token: Terraform user token
    :param workspace_id: Terraform workspace ID, can get this ID using get_workspace function or after Terraform
    workspace creation
    :param auto_queue: if set True, Terraform automatically queues runs when new commits are merged.
    :return: API response
    """
    payload = {"data": {"type": "configuration-versions", "attributes": {"auto-queue-runs": auto_queue}}}
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/workspaces/{workspace_id}/configuration-versions"
    try:
        req = requests.post(url, json=payload, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def workspace_upload_code(token: str, filepath: str, upload_url: str):
    """
    Upload Terraform code in .tar.gz type, to Terraform configuration version
    Construct API request and send API request for uploading Terraform .tar.gz file
    to Terraform workspace configuration version
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/configuration-versions#upload-configuration-files
    :param upload_url: Terraform configuration version url, can get this from Terraform workspace configuration version
    creation or workspace_config_get function
    :param filepath: path to .tar.gz contains Terraform code files
    :param token: Terraform user token
    :return: API response
    """
    header = {"Content-type": "application/octet-stream", "Authorization": f"Bearer {token}"}
    url = upload_url
    if not exists(filepath):
        raise SystemExit('File path to Terraform .tar.gz file not exist')

    file = [('file', open(filepath, "rb"))]
    try:
        req = requests.put(url, headers=header, files=file,verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def payload_tf_run(var_name: str, val: str, description, hcl: bool, sensitive: bool):
    """
    TODO: refactor this
    construct terraform run payload, can only create 1 variable at once
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspace-variables
    :param var_name: string, variable name
    :param val: string, variable value
    :param description: string, description of the variable
    :param hcl: bool, parse this variable as HCL, allow to interpolate at run time
    :param sensitive: bool, sensitive variable are never shown in UI or API
    :return: dict, JSON payload
    """
    payload = {"data": {"type": "vars", "attributes": {"key": var_name, "value": val, "description": description,
                                                       "category": "terraform", "hcl": hcl, "sensitive": sensitive}}}
    return payload
