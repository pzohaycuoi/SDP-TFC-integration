import os
import stat
from dotenv import load_dotenv
import datetime


def cleanup_temp(top):
    """
    Cleanup repository folder after run complete
    :param top: folder path
    """
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)
    # os.mkdir(top)


def dotenv_load():
    """
    Load .env file contains all sensitive informations
    """
    config = load_dotenv()
    TF_TOKEN = os.getenv("TF_TOKEN")
    TF_ORG = os.getenv("TF_ORG")
    TF_SERVER = os.getenv("TF_SERVER")
    GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
    GITLAB_REPO_ID = os.getenv("GITLAB_REPO_ID")
    GITLAB_NAMESPACE = os.getenv("GITLAB_NAMESPACE")
    GITLAB_SERVER = os.getenv("GITLAB_SERVER")
    REPO = os.getenv("REPO")
    OAUTH_TOKEN_ID = os.getenv("OAUTH_TOKEN_ID")
    SDP_TOKEN = os.getenv("SDP_TOKEN")
    SDP_SERVER = os.getenv("SDP_SERVER")

    if (TF_TOKEN == '') or (TF_TOKEN is None):
        raise ValueError("No dotenv with name TOKEN provided, exiting...")
    elif (TF_ORG == '') or (TF_ORG is None):
        raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
    elif (GITLAB_TOKEN == '') or (GITLAB_TOKEN is None):
        raise SystemExit("No dotenv with name TOKEN provided, exiting...")
    elif (GITLAB_REPO_ID == '') or (GITLAB_REPO_ID is None):
        raise SystemExit("No dotenv with name GITLAB_REPO_ID provided, exiting...")
    elif (GITLAB_NAMESPACE == '') or (GITLAB_NAMESPACE is None):
        raise SystemExit("No dotenv with name GITLAB_NAMESPACE provided, exiting...")
    elif (REPO == '') or (REPO is None):
        raise SystemExit("No dotenv with name REPO provided, exiting...")
    elif (OAUTH_TOKEN_ID == '') or (OAUTH_TOKEN_ID is None):
        raise SystemExit("No dotenv with name OAUTH_TOKEN_ID provided, exiting...")
    elif (SDP_TOKEN == '') or (SDP_TOKEN is None):
        raise SystemExit("No dotenv with name SDP_TOKEN provided, exiting...")
    elif (SDP_SERVER == '') or (SDP_SERVER is None):
        raise SystemExit("No dotenv with name SDP_SERVER provided, exiting...")
    elif (TF_SERVER == '') or (TF_SERVER is None):
        raise SystemExit("No dotenv with name TF_SERVER provided, exiting...")
    elif (GITLAB_SERVER == '') or (GITLAB_SERVER is None):
        raise SystemExit("No dotenv with name GITLAB_SERVER provided, exiting...")
    else:
        return TF_TOKEN, TF_ORG, GITLAB_TOKEN, GITLAB_REPO_ID, GITLAB_NAMESPACE, REPO, OAUTH_TOKEN_ID, SDP_TOKEN, \
               SDP_SERVER, TF_SERVER, GITLAB_SERVER


def folder_create(name: str, path: str):
    current_time = datetime.datetime.now()
    str_time = current_time.strftime("%d-%m-%Y-%H-%M-%S")
    folder_name = f"{name}-{str_time}"
    folder_path = os.path.join(path, folder_name)
    # folder_path = f"{path}{folder_name}/"

    if os.path.exists(folder_path):
        return folder_path
    else:
        try:
            os.mkdir(folder_path)
        except OSError as err:
            SystemExit(err)

        return folder_path
