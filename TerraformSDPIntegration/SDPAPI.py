import json
import requests
from os.path import exists


def task_add(token: str, server: str, change_id: str, task_name: str, task_description: str):
    """
    API request for creating new task for a change ticket
    :param token: SDP user API token
    :param server: SDP server url
    :param change_id: SDP change ID number
    :param task_name: name of the task
    :param task_description: description of the task
    :return: Task ID
    """
    input_data = """{
        "task": {
            "title": "%s",
            "description": "%s",
            "status": {
                "name": "Open"
            },
            "change": {
                "id": %s
            }
        }
    }""" % (task_name, task_description, change_id)
    payload = {'input_data': input_data}
    header = {"technician_key": token}
    url = f"{server}/api/v3/tasks"
    try:
        req = requests.post(url, data=payload, headers=header, verify=False)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    req.raise_for_status()
    data = json.loads(req.content)
    task_id = data["task"]["id"]
    return task_id


def task_update(token: str, server: str, task_id: str, status: str):
    input_data = """{
        "task": {
            "status": {
                "name": "%s"
            }
        }
    }""" % status
    payload = {'input_data': input_data}
    header = {"technician_key": token}
    url = f"{server}/api/v3/tasks/{task_id}"
    try:
        req = requests.put(url, data=payload, headers=header, verify=False)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    req.raise_for_status()
    data = json.loads(req.content)
    task_id = data["task"]["id"]
    return task_id


def worklog_add(token: str, server: str, task_id: str, description: str, time_start, time_end):
    """
    Add worklog and attach it to a task on SDP
    :param token: technician API token
    :param server: SDP API server
    :param task_id: SDP task id
    :param description: description for SDP worklog
    :param time_start: time start of the worklog
    :param time_end: time end of the worklog
    :return: worklog id
    """
    input_data = '{"worklog": {"task": {"id": "%s"},"description": "%s","technician": {"name": "administrator"},' \
                 '"start_time": {"value": "%s"},"end_time": {"value": "%s"}}}' % (task_id, description, time_start,
                                                                                  time_end)
    payload = {"input_data": input_data}
    header = {"technician_key": token}
    url = f"{server}/api/v3/worklog"
    try:
        req = requests.post(url, data=payload, headers=header, verify=False)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    req.raise_for_status()
    data = json.loads(req.content)
    worklog_id = data["worklog"]["id"]
    return worklog_id


def task_attachment_add(token: str, server: str, task_id: str, file_path: str):
    input_data = """{
            "attachment": {
                "task": {
                    "id": "%s"
                }
            }
        }""" % task_id
    payload = {"input_data": input_data}
    header = {"technician_key": token}
    url = f"{server}/api/v3/attachments"
    if not exists(file_path):
        raise SystemExit('File path to Terraform .tar.gz file not exist')
    else:
        file = [('file', open(file_path, "rb"))]

    try:
        req = requests.post(url, data=payload, headers=header, files=file)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    req.raise_for_status()
