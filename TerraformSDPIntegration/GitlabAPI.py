import requests
import json


def project_fork(token: str, server: str, project_id: str, project_name: str, namespace: str):
    """
    Fork a Gitlab project, use this to create a repository for Terraform workspace
    Construct API request and send API request for forking Gitlab project
    :param namespace: Gitlab namespace
    :param server: Gitlab server url
    :param token: Gitlab access token with API permission
    :param project_id: Gitlab project id used to fork
    :param project_name:
    :return:
    """
    payload = {"name": project_name, "namespace_path": namespace, "path": project_name}
    header = {"PRIVATE-TOKEN": token}
    url = f"{server}/api/v4/projects/{project_id}/fork"
    try:
        req = requests.post(url, json=payload, headers=header, verify=True)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    req.raise_for_status()
    return json.loads(req.text)


def project_get(token: str, server: str, project_name=None, project_id=None):
    """
    Get Gitlab project detail information, use this to check if the project is already created or not
    Construct API request and send API request for getting a Gitlab project information
    :param project_id: Gitlab project ID
    :param server: Gitlab server url
    :param token: Gitlab user access token
    :param project_name: Gitlab project name
    :return: Gitlab project detail
    """
    if (project_id is None) and (project_name is not None):
        header = {"Content-type": "application/vnd.api+json", "PRIVATE-TOKEN": f"{token}"}
        url = f"{server}/api/v4/projects?owned=true&search={project_name}"
        try:
            req = requests.get(url, headers=header, verify=True)
        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        req.raise_for_status()
        return req
    elif (project_id is not None) and (project_name is None):
        header = {"Content-type": "application/vnd.api+json", "PRIVATE-TOKEN": f"{token}"}
        url = f"{server}/api/v4/projects/{project_id}/"
        try:
            req = requests.get(url, headers=header, verify=True)
        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        req.raise_for_status()
        return req
    else:
        raise SystemExit(f"No project id and project name provided, exiting...")
