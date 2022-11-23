import requests
from os.path import exists


def creation(token: str, terraform_org: str, workspace_name: str, auto_apply: bool):
    """
    Construct API payload for Terraform workspace creation.
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces
    :param terraform_org:
    :param token:
    :param workspace_name: string
    :param auto_apply: bool
    :return: dict
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


def config(token: str, workspace_id: str, auto_queue: bool):
    """
    Construct API payload for config Terraform workspace configuration versions
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/configuration-versions#create-a-configuration-version
    :param token:
    :param workspace_id:
    :param auto_queue:
    :return:
    """
    payload = {"data": {"type": "configuration-versions", "attributes": {"auto-queue-runs": auto_queue}}}
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/workspaces/{workspace_id}/configuration-versions"
    try:
        req = requests.post(url, json=payload, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def upload_code(token: str, filepath: str, upload_url: str):
    """
    Construct API payload for config Terraform workspace configuration versions
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/configuration-versions#upload-configuration-files
    :param upload_url:
    :param filepath:
    :param token:
    :return:
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
