import TerraformApi
import common
import os
import json
import sys
from subprocess import Popen

# Load .env file and
TF_TOKEN, TF_ORG, GITLAB_TOKEN, GITLAB_REPO_ID, GITLAB_NAMESPACE, REPO, OAUTH_TOKEN_ID, SDP_TOKEN, SDP_SERVER, \
    TF_SERVER, GITLAB_SERVER = common.dotenv_load()

# Load needed data left by TerraformFetchPlanStatus.py
cur_dir = os.path.dirname(__file__)
temp_file = os.path.join(cur_dir, "../temp/trigger.json")
if not os.path.exists(temp_file):
    raise SystemExit(f"NO DATA FILE FOUND: {temp_file}")

data = json.loads(temp_file)
if data is None:
    raise SystemExit(f"FILE IS EMPTY: {temp_file}")
elif "run_id" not in data:
    raise SystemExit(f"NO TERRAFORM run_id IN: {temp_file}")
elif "change_id" not in data:
    raise SystemExit(f"NO SDP change_id IN: {temp_file}")
elif "folder_path" not in data:
    raise SystemExit(f"NO SDP folder_path IN: {temp_file}")

# Get the Terraform run ID and trigger apply the run
run_id = data["run_id"]
change_id = data["change_id"]
folder_path = data["folder_path"]
comment = f"SDP change number: {change_id}"
TerraformApi.tf_run_apply(TF_TOKEN, TF_SERVER, run_id, comment)

# Spawn new process to fetch Terraform apply status
next_script = os.path.join(cur_dir, "TerraformFetchRunStatus.py")

if sys.platform == "win32":
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    DETACHED_PROCESS = 0x00000008
    command = ["python", next_script, folder_path]
    Popen(command, stdin=None, stdout=None, stderr=None, shell=True,
          creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
else:
    command = ["python3", next_script, folder_path]
    Popen(command, stdin=None, stdout=None, stderr=None, shell=True)
