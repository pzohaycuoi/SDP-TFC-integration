from dotenv import load_dotenv
import os
import json
import TerraformApi
import SDP
import VCS
import tarfile
from subprocess import Popen


# LOADING DATA FROM SDP AND .ENV
# load .env file and
# check if TOKEN and TF_ORG have value
config = load_dotenv()
TOKEN = os.getenv("TOKEN")
TF_ORG = os.getenv("TF_ORG")
REPO = os.getenv("REPO")

if (TOKEN == '') or (TOKEN is None):
    raise SystemExit("No dotenv with name TOKEN provided, exiting...")
elif (TF_ORG == '') or (TF_ORG is None):
    raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
elif (REPO == '') or (REPO is None):
    raise SystemExit("No dotenv with name TF_ORG provided, exiting...")

# PARSING SDP TICKET INFORMATION #
# Get Terraform code from repository
tar_file = VCS.git_clone_and_tar(REPO, "../temp")

# get variable list
var_files = VCS.find_all("variables.tf", "../temp")

var_list = []
for file in var_files:
    var_in_file = VCS.get_tf_var(file)
    for s in var_in_file:
        var_list.append(s)

# get unique value from var_list[] by converting to set
var_list = set(var_list)
var_list = list(var_list)

# load $COMPLETE_JSON_FILE from SDP
# input_file = sys.argv[1]
input_file = '../test/test-data.json'  # for testing only
try:
    opt_data = SDP.convert_json(input_file)
except AssertionError as err:
    raise SystemExit(err)

# Get SDP custom field values, base on Terraform variable file
field_list = SDP.get_field(opt_data)
field_name_list = list(field_list.keys())
matching_field_name = [field for field in field_name_list if field in var_list]
matching_field = {}

for field in field_list:
    if field in matching_field_name:
        matching_field.update({field: field_list[field]})
    elif field == "workspace_name":
        matching_field.update({field: field_list[field]})
    elif field == "Environment":
        matching_field.update({field: field_list[field]})

# TERRAFORM WORKSPACE CREATION AND CONFIGURATION #
# Check if workspace field hs value
workspace_name = matching_field["workspace_name"]

if (workspace_name == '') or (workspace_name is None):
    SystemExit("No Terraform workspace name provided, exiting...")
else:
    workspace_get = TerraformApi.workspace_get(TOKEN, TF_ORG, workspace_name)
    if workspace_get.status_code == 400:
        SystemExit("User token does not have permission or token invalid")
    elif workspace_get.status_code == 200:
        workspace_get_json = json.loads(workspace_get)
        workspace_id = workspace_get_json["data"]["id"]
        # Check if workspace have configuration version yet

        SystemExit("Terraform workspace name is already exist, please pick other name, exiting...")
    else:
        # Create Terraform workspace
        workspace_create = TerraformApi.workspace_create(TOKEN, TF_ORG, workspace_name, auto_apply=False)
        workspace_create.raise_for_status()
        workspace_create_json = json.loads(workspace_create.content)
        workspace_id = workspace_create_json["data"]["id"]

# TODO: If workspace is already created, check if workspace have configuration version
# Create Terraform configuration version
workspace_conf_create = TerraformApi.workspace_config_create(TOKEN, workspace_id, auto_queue=False)
workspace_conf_create.raise_for_status()
workspace_conf_json = json.loads(workspace_conf_create.content)
workspace_upload_url = workspace_conf_json["data"]["attributes"]["upload-url"]

# Get upload url from configuration version and upload Terraform code into workspace
workspace_conf_upload = TerraformApi.workspace_upload_code(TOKEN, tar_file, workspace_upload_url)

# SETTING UP WORKSPACE VARIABLES AND VARIABLE SETS #
# Set variables of workspace (TFvars)
for field in matching_field:
    if (field != "Environment") and (field != "workspace_name"):
        workspace_var_create = TerraformApi.workspace_var_create(TOKEN, field, matching_field[field], workspace_id)
        workspace_var_create.raise_for_status()
    else:
        continue

# Get variable set name from config file
try:
    config_data = SDP.convert_json("../config/config.json")
except AssertionError as err:
    raise SystemExit(err)

varset_name = ""
if matching_field["Environment"] in config_data["variable-set"]:
    varset_name = config_data["variable-set"][matching_field["Environment"]]
else:
    SystemExit("SDP ticket: provided Environment field doesn't match any variable set in config.json")

# Get variable set ID
varset_id = TerraformApi.tf_varset_get(TOKEN, varset_name, TF_ORG)

if varset_id == "":
    SystemExit("SDP ticket: provided Environment field doesn't match any variable set in Terraform environment")
else:
    workspace_varset = TerraformApi.workspace_varset_set(TOKEN, varset_id, workspace_id=workspace_id)
    workspace_varset.raise_for_status()

# TERRAFORM RUN
# After finished setting up Terraform workspace, workspace variable, variable set, create the Terraform run
# Terraform created by this script set the auto-apply == false, so after Terraform plan, it will wait for confirmation
tf_run = TerraformApi.workspace_run(TOKEN, workspace_id)
tf_run.raise_for_status()
tf_run_json = json.loads(tf_run)

# Because SDP only script run up to 60 seconds, so we pass data into a temp file and create a new independent process
with open("..temp/temp.json", "w") as file:
    file.write(tf_run_json)

CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008

Popen(["python", "./TerraformRunFetchStatus.py"],
      stdin=None, stdout=None, stderr=None, shell=True,
      creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
