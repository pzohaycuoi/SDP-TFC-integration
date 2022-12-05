import os
import stat
from dotenv import load_dotenv


def cleanup_temp(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)
    os.mkdir(top)


def dotenv_load():
    config = load_dotenv()
    TF_TOKEN = os.getenv("TF_TOKEN")
    TF_ORG = os.getenv("TF_ORG")
    GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
    GITLAB_REPO_ID = os.getenv("GITLAB_REPO_ID")
    GITLAB_NAMESPACE = os.getenv("GITLAB_NAMESPACE")
    REPO = os.getenv("REPO")
    OAUTH_TOKEN_ID = os.getenv("OAUTH_TOKEN_ID")

    if (TF_TOKEN == '') or (TF_TOKEN is None):
        raise SystemExit("No dotenv with name TOKEN provided, exiting...")
    elif (TF_ORG == '') or (TF_ORG is None):
        raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
    elif (GITLAB_TOKEN == '') or (GITLAB_TOKEN is None):
        raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
    elif (GITLAB_REPO_ID == '') or (GITLAB_REPO_ID is None):
        raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
    elif (GITLAB_NAMESPACE == '') or (GITLAB_NAMESPACE is None):
        raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
    elif (REPO == '') or (REPO is None):
        raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
    elif (OAUTH_TOKEN_ID == '') or (OAUTH_TOKEN_ID is None):
        raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
    else:
        return TF_TOKEN, TF_ORG, GITLAB_TOKEN, GITLAB_REPO_ID, GITLAB_NAMESPACE, REPO, OAUTH_TOKEN_ID