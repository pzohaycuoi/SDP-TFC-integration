import os
import json
import TerraformApi
import SDP
import VCS
import common
from subprocess import Popen
import GitlabAPI
import sys


# load $COMPLETE_JSON_FILE from SDP
# input_file = sys.argv[1]  # uncomment this after testing is done
input_file = '../test/test-data.json'  # for testing only, comment this line after done testing
try:
    opt_data = SDP.convert_json(input_file)
except AssertionError as err:
    raise SystemExit(err)

# VALIDATE INPUT AND CHECK RESOURCE EXISTENCE
# load .env file and
# check if TOKEN and TF_ORG have value
TF_TOKEN, TF_ORG, GITLAB_TOKEN, GITLAB_REPO_ID, GITLAB_NAMESPACE, REPO, OAUTH_TOKEN_ID, SDP_TOKEN, SDP_SERVER, \
    TF_SERVER, GITLAB_SERVER = common.dotenv_load()
cur_dir = os.path.dirname(__file__)
repo_dir = os.path.join(cur_dir, "../temp/repo")

# Clean up repo dir before cloning
if os.path.exists(repo_dir):
    common.cleanup_temp(repo_dir)

# Get Terraform code from repository
VCS.git_clone_and_tar(REPO, repo_dir)

# Get Terraform variables.tf file list
var_files = VCS.find_all("variables.tf", repo_dir)

# Extract variables from Terraform variables.tf files
var_list = []
for file in var_files:
    var_in_file = VCS.get_tf_var(file)
    for s in var_in_file:
        var_list.append(s)

# get unique value from var_list[] by converting to set
var_list = set(var_list)
var_list = list(var_list)

# Get SDP custom field values, base on Terraform variable file
field_list = SDP.get_field(opt_data)
field_name_list = list(field_list.keys())
matching_field_name = [field for field in field_name_list if field in var_list]
matching_field = {}

# workspace_name and Environment field are not in variables.tf, they are SDP fields, so insert them to the dict
for field in field_list:
    if field in matching_field_name:
        matching_field.update({field: field_list[field]})
    elif field == "workspace_name":
        if field_list[field] == "":
            raise SystemExit("Workspace is not provided, exiting..")
        else:
            matching_field.update({field: field_list[field]})
    elif field == "Environment":
        if field_list[field] == "":
            raise SystemExit("Environment is not provided, exiting..")
        else:
            matching_field.update({field: field_list[field]})

# Clean up repo folder
if os.path.exists(repo_dir):
    common.cleanup_temp(repo_dir)

# Get variable set name from config file
try:
    config_file = os.path.join(cur_dir, "../config/config.json")
    config_data = SDP.convert_json(config_file)
except AssertionError as err:
    raise SystemExit(err)

# Check if there is any varset for provided environment
workspace_name = matching_field["workspace_name"]
environment = matching_field["Environment"]
varset_name = ""

# TODO: add health check
# Check if provided git lab project id exist:
repo_check = GitlabAPI.project_get(GITLAB_TOKEN, GITLAB_SERVER, project_id=GITLAB_REPO_ID)

if repo_check.status_code == 404:
    raise SystemExit("Provided Gitlab project ID is not exist, exiting...")
elif repo_check.status_code == 402:
    raise SystemExit("Provided Gitlab token doesn't have enough permission, exiting...")

if environment not in config_data["variable-set"]:
    raise SystemExit("SDP ticket: provided Environment field doesn't match any variable set in config.json")

varset_name = config_data["variable-set"][environment]

# Get variable set ID
varset_id, varset_relationship = TerraformApi.tf_varset_get(TF_TOKEN, TF_SERVER, varset_name, TF_ORG)
if varset_id == "":
    raise SystemExit("SDP ticket: provided Environment field doesn't match any variable set in Terraform environment")

# TERRAFORM WORKSPACE CREATION AND CONFIGURATION #
workspace_name = f"{workspace_name}-{environment}"  # construct workspace name with environment
workspace_get = TerraformApi.workspace_get(TF_TOKEN, TF_SERVER, TF_ORG, workspace_name)
if workspace_get.status_code == 401:
    raise SystemExit("User token does not have permission or token invalid")
elif (workspace_get.status_code == 201) or (workspace_get.status_code == 200):
    workspace_get = json.loads(workspace_get.text)
    workspace_id = workspace_get["data"]["id"]
else:
    # Create Terraform workspace
    workspace_get = TerraformApi.workspace_create(TF_TOKEN, TF_SERVER, TF_ORG, workspace_name, auto_apply=False)
    workspace_id = workspace_get["data"]["id"]

# Check if TF workspace attach to any repo, if not then fork provided repo and attach it to the workspace
if workspace_get["data"]["attributes"]["vcs-repo"] is None:
    project_name = workspace_name
    project_get = GitlabAPI.project_get(GITLAB_TOKEN, GITLAB_SERVER, project_name)
    project_get = json.loads(project_get.text)
    if not project_get:
        project_fork = GitlabAPI.project_fork(GITLAB_TOKEN, GITLAB_SERVER, GITLAB_REPO_ID, project_name,
                                              GITLAB_NAMESPACE)
        project_url = project_fork["path_with_namespace"]
    else:
        project_url = project_get[0]["path_with_namespace"]

    TerraformApi.workspace_add_repo(TF_TOKEN, TF_SERVER, workspace_id, project_url, OAUTH_TOKEN_ID)

# SETTING UP WORKSPACE VARIABLES AND VARIABLE SETS #
# Set variables of workspace (TFvars)
workspace_var_check = TerraformApi.workspace_var_get(TF_TOKEN, TF_SERVER, TF_ORG, workspace_name)
if not workspace_var_check["data"]:
    for field in matching_field:
        if (field != "Environment") and (field != "workspace_name"):
            TerraformApi.workspace_var_create(TF_TOKEN, TF_SERVER, field, matching_field[field], workspace_id)
        else:
            continue
else:
    workspace_matching_vars = []
    for var in workspace_var_check["data"]:
        if var["attributes"]["key"] in matching_field:
            k = var["attributes"]["key"]
            v = matching_field[k]
            workspace_matching_vars.append(k)

            if var["attributes"]["value"] != v:
                TerraformApi.workspace_var_update(TF_TOKEN, TF_SERVER, var["id"], k, v)
            else:
                continue

    for k in matching_field:
        v = matching_field[k]
        if (k != "Environment") and (k != "workspace_name"):
            if k not in workspace_matching_vars:
                TerraformApi.workspace_var_create(TF_TOKEN, TF_SERVER, k, v, workspace_id)
            else:
                continue

varset_workspace_list = []
for workspace in varset_relationship:
    if workspace_id == workspace["id"]:
        varset_workspace_list.append(workspace["id"])
        break
    else:
        varset_workspace_list.append(workspace["id"])
        continue

if workspace_id not in varset_workspace_list:
    TerraformApi.workspace_varset_set(TF_TOKEN, TF_SERVER, varset_id, workspace_id)

# Create workspace notification config
tf_team_id = TerraformApi.team_get(TF_TOKEN, TF_SERVER, "owners", TF_ORG)
tf_user_id_list = TerraformApi.team_member_get(TF_TOKEN, TF_SERVER, tf_team_id)
TerraformApi.notification_set(TF_TOKEN, TF_SERVER, workspace_id, tf_user_id_list)

# TERRAFORM RUN
# After finished setting up Terraform workspace, workspace variable, variable set, create the Terraform run
# Terraform created by this script set the auto-apply == false, so after Terraform plan,
# it will wait for confirmation
tf_run = TerraformApi.workspace_run(TF_TOKEN, TF_SERVER, workspace_id)

# Because SDP only script run up to 60 seconds, so we pass data into a temp file and
# Create folder
temp_folder = os.path.join(cur_dir, "../temp/")
folder = common.folder_create(workspace_name, temp_folder)

# Save run data so new process have something to do
temp_file = os.path.join(folder, "temp.json")
with open(f"{temp_file}", "w") as file:
    file.write(tf_run)

# Gather some data into file for new process
tf_run_json = json.loads(tf_run)
change_id = opt_data["INPUT_DATA"]["entity_data"]["template"]["id"]
run_id = tf_run_json["data"]["id"]
data = '''{
    "workspace_name": "%s",
    "change_id": %s,
    "folder_path": "%s"
    "run_id": "%s"
}''' % (workspace_name, change_id, folder, run_id)
data_file = os.path.join(folder, "data.json")
with open(data_file, "w") as file:
    file.write(data)

temp_file = os.path.join(temp_folder, "trigger.json")
if os.path.exists(temp_file):
    os.remove(temp_file)

with open(temp_file, "w") as file:
    file.write(data)

# file path to the next script
next_script = os.path.join(cur_dir, "TerraformFetchPlanStatus.py")

# Check platform and create independent process
if sys.platform == "win32":
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    DETACHED_PROCESS = 0x00000008
    command = ["python", next_script, folder]
    Popen(command, stdin=None, stdout=None, stderr=None, shell=True,
          creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
else:
    command = ["python3", next_script, folder]
    Popen(command, stdin=None, stdout=None, stderr=None, shell=True)
