import requests
from os.path import exists
import json


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
    url = f"https://app.terraform.io/api/v2/organizations/{terraform_org}/workspaces/{workspace_name}/"
    try:
        req = requests.get(url, headers=header, verify=True)
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


def workspace_config_get(token: str, config_id: str):
    """
    Get Terraform workspace configuration version information through API request
    Construct API request and send API request for getting the workspace configuration version information
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/configuration-versions#show-a-configuration-version
    :param token: Terraform user token
    :param config_id: Terraform configuration id
    :return: API response
    """
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/configuration-versions/{config_id}/"
    try:
        req = requests.get(url, headers=header, verify=True)
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
    else:
        file = [('file', open(filepath, "rb"))]

    try:
        req = requests.put(url, headers=header, files=file, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def workspace_var_create(token: str, var_name: str, var_val: str, workspace_id: str, hcl=False, sensitive=False,
                         description=None):
    """
    construct terraform run payload, can only create 1 variable at once
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspace-variables
    :param token: Terraform user token
    :param var_name: variable name
    :param var_val: variable value
    :param workspace_id: Terraform's workspace ID get from Terraform's API
    :param description: description of the variable
    :param hcl: parse this variable as HCL, allow to interpolate at run time
    :param sensitive: sensitive variable are never shown in UI or API
    :return: API response
    """
    if description is not None:
        payload = {
            "data": {"type": "vars", "attributes": {"key": var_name, "value": var_val, "description": description,
                                                    "category": "terraform", "hcl": hcl,
                                                    "sensitive": sensitive}}}
    else:
        payload = {"data": {"type": "vars", "attributes": {"key": var_name, "value": var_val, "category": "terraform",
                                                           "hcl": hcl, "sensitive": sensitive}}}

    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/workspaces/{workspace_id}/vars"
    try:
        req = requests.post(url, json=payload, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def workspace_varset_set(token: str, varset_id: str, workspace_id: str):
    """
    Attach Terraform variable set to a workspace
    Construct API request and send API request for attaching variable set to Terraform workspace
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variable-sets#apply-variable-set-to-workspaces
    :param token: Terraform user token
    :param varset_id: variable set ID get from tf_varset_get func
    :return: API response
    """
    payload = {"data": [{"type": "workspaces", "id": f"{workspace_id}"}]}
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/varsets/{varset_id}/relationships/workspaces/"
    try:
        req = requests.post(url, json=payload, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def tf_varset_get(token: str, varset_name: str, terraform_org: str):
    """
    Get Terraform variable set ID from variable set name
    Construct API request and send API request for getting the variable set id from provided variable set name
    in Terraform organization
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variable-sets#show-variable-set
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variable-sets#list-variable-set
    :param token: Terraform user token
    :param varset_name: Terraform organization variable set name
    :param terraform_org: Terraform organization name
    :return: Terraform variable set id
    """
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    varset_id = ""
    relationships = None
    i = 0
    while True:
        i += 1
        url = f"https://app.terraform.io/api/v2/organizations/{terraform_org}/varsets/?page%5Bnumber%5D={i}&page%5Bsize%5D=100"
        try:
            req = requests.get(url, headers=header, verify=True)
        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        res = json.loads(req.text)
        if varset_id == "":
            for data in res['data']:
                if data["attributes"]["name"] == varset_name:
                    varset_id = data["id"]
                    relationships = data["relationships"]["workspaces"]["data"]
                    break
        else:
            break

    return varset_id, relationships


def workspace_run(token: str, workspace_id: str):
    """
    Create a Terraform workspace run, a run flow contains Terraform plan: check policies, cost estimation if it's a
    cloud provider, Terraform apply: run apply the Terraform, making changes/provisioning the resources.
    Construct API request and send API request for launching the Terraform run of a workspace
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run#attributes
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run#create-a-run
    :param token: Terraform user token
    :param workspace_id: Terraform workspace id
    :return: API response
    """
    payload = {"data": {"types": "runs", "relationships": {"workspace": {"data": {"type": "workspaces",
                                                                                  "id": workspace_id}}}}}
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/runs"
    try:
        req = requests.post(url, json=payload, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def tf_run_get(token: str, run_id: str):
    """
    Fetch Terraform run status
    Construct API request and send API request for fetching the Terraform run of a workspace
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run#get-run-details
    :param token: Terraform user token
    :param run_id: Terraform run ID, generated after a Terraform run created
    :return: API response
    """
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/runs/{run_id}"
    try:
        req = requests.get(url, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def workspace_add_repo(token: str, workspace_id: str, repo_url: str, gitlab_token: str):
    """
    Add a VCS to Terraform workspace configuration
    Construct API request and send API request for updating the Terraform workspace configuration
    :param token: Terraform user token
    :param workspace_id: Terraform workspace ID
    :param repo_url: gitlab repository url
    :param gitlab_token: Gitlab access token
    :return: Terraform workspace information
    """
    payload = {"data": {"attributes": {"vcs-repo": {"identifier": repo_url, "oauth-token-id": gitlab_token}}}}
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/workspaces/{workspace_id}"
    try:
        req = requests.patch(url, json=payload, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return req


def workspace_var_get(token: str, terraform_org: str, workspace_name: str):
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/vars?filter%5Borganization%5D%5Bname%5D={terraform_org}&filter%5Bworkspace%5D%5Bname%5D={workspace_name}"
    try:
        req = requests.get(url, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    data = json.loads(req.content)
    return data


def workspace_var_update(token: str, var_id: str, var_name: str, var_value: any):
    payload = {"data": {"id": var_id, "attributes": {"key": var_name, "value": var_value}, "type": "vars"}}
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/vars/{var_id}"
    try:
        req = requests.patch(url, json=payload,headers=header, verify=True)
    except requests.exceptions.HTTPError as err:
        raise requests.exceptions.RequestException

    return req.status_code


def tf_notification_set(token: str, workspace_id: str, user_id_list: str):
    payload = {
          "data": {
            "type": "notification-configurations",
            "attributes": {
              "destination-type": "email",
              "enabled": "True",
              "name": "Notify organization users about run",
              "triggers": [
                "run:applying",
                "run:completed",
                "run:created",
                "run:errored",
                "run:needs_attention",
                "run:planning"
              ]
            },
            "relationships": {
               "users": {
                  "data": user_id_list
               }
            }
          }
        }
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    url = f"https://app.terraform.io/api/v2/workspaces/{workspace_id}/notification-configurations"
    try:
        req = requests.post(url, json=payload, headers=header, verify=True)
    except requests.exceptions.HTTPError as err:
        raise requests.exceptions.RequestException

    return req.status_code


def tf_team_get(token : str, group_name: str, terraform_org: str):
    """

    :param token:
    :param group_name:
    :param terraform_org:
    :return:
    """
    url = f"https://app.terraform.io/api/v2/organizations/{terraform_org}/teams"
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    i = 0
    team_id = ""
    while True:
        i += 1
        url = f"https://app.terraform.io/api/v2/organizations/{terraform_org}/teams?page%5Bnumber%5D={i}&page%5Bsize%5D=100"
        try:
            req = requests.get(url, headers=header, verify=True)
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

        res = json.loads(req.text)
        if team_id == "":
            for data in res['data']:
                if data["attributes"]["name"] == group_name:
                    team_id = data["id"]
                    break
        else:
            break

    return team_id


def tf_team_member_get(token: str, team_id: str):
    url = f"https://app.terraform.io/api/v2/teams/{team_id}"
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    try:
        req = requests.get(url, headers=header, verify=True)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    data = json.loads(req.content)
    user_list = []

    if data["data"] is None:
        SystemExit()
    elif "relationships" not in data["data"]:
        SystemExit()
    elif data["data"]["relationships"]["users"]["data"] is None:
        SystemExit()
    else:
        users = data["data"]["relationships"]["users"]["data"]
        for user in users:
            if user["type"] == "users":
                user_list.append(user)
            else:
                continue

    return user_list


def tf_plan_get(token: str, plan_id: str, file_name: str):
    """
    When Terraform plan status is "finished", Terraform plan result will be available to check.
    Get Terraform plan result detail in json
    :param token: Terraform user token
    :param plan_id: Terraform plan id
    :return: Terraform plan result in JSON
    """
    url = f"https://app.terraform.io/api/v2/runs/{plan_id}/plan/json-output"
    header = {"Content-type": "application/vnd.api+json", "Authorization": f"Bearer {token}"}
    try:
        req = requests.get(url, headers=header, verify=True)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    with open(file_name, "w") as file:
        file.write(req.text)

