from dotenv import load_dotenv
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
    tf_workspace_name = matching_field["workspace_name"]
    environment = matching_field["Environment"]
    tf_varset_name = ""

    # TODO: add health check
    # Check if provided git lab project id exist:
    gitlab_provided_check = GitlabAPI.project_get(GITLAB_TOKEN, project_id=GITLAB_REPO_ID)

    if gitlab_provided_check.status_code == 404:
        raise SystemExit("Provided Gitlab project ID is not exist, exiting...")
    elif gitlab_provided_check.status_code == 402:
        raise SystemExit("Provided Gitlab token doesn't have enough permission, exiting...")

    if environment not in config_data["variable-set"]:
        raise SystemExit("SDP ticket: provided Environment field doesn't match any variable set in config.json")
    else:
        tf_varset_name = config_data["variable-set"][environment]

        # Get variable set ID
        tf_varset_id, tf_varset_relationships = TerraformApi.tf_varset_get(TF_TOKEN, tf_varset_name, TF_ORG)

        if tf_varset_id == "":
            raise SystemExit("SDP ticket: provided Environment field doesn't match any variable set in Terraform environment")
        else:
            # TERRAFORM WORKSPACE CREATION AND CONFIGURATION #
            tf_workspace_name = f"{tf_workspace_name}-{environment}"  # construct workspace name with environment
            tf_workspace_get = TerraformApi.workspace_get(TF_TOKEN, TF_ORG, tf_workspace_name)

            if tf_workspace_get.status_code == 401:
                raise SystemExit("User token does not have permission or token invalid")
            elif (tf_workspace_get.status_code == 201) or (tf_workspace_get.status_code == 200):
                tf_workspace_get_json = json.loads(tf_workspace_get.content)
                tf_workspace_id = tf_workspace_get_json["data"]["id"]
            else:
                # Create Terraform workspace
                tf_workspace_create = TerraformApi.workspace_create(TF_TOKEN, TF_ORG, tf_workspace_name, auto_apply=False)
                tf_workspace_create.raise_for_status()
                tf_workspace_get_json = json.loads(tf_workspace_create.content)
                tf_workspace_id = tf_workspace_get_json["data"]["id"]

            if tf_workspace_get_json["data"]["attributes"]["vcs-repo"] is None:
                gitlab_project_name = tf_workspace_name
                gitlab_project_get = GitlabAPI.project_get(GITLAB_TOKEN, gitlab_project_name)
                gitlab_project_get_json = json.loads(gitlab_project_get.content)
                if not gitlab_project_get_json:
                    gitlab_project_fork = GitlabAPI.project_fork(GITLAB_TOKEN, GITLAB_REPO_ID, gitlab_project_name,
                                                                 GITLAB_NAMESPACE)
                    gitlab_project_fork.raise_for_status()
                    gitlab_project_fork = json.loads(gitlab_project_fork.content)
                    gitlab_project_url = gitlab_project_fork["path_with_namespace"]
                else:
                    gitlab_project_url = gitlab_project_get_json[0]["path_with_namespace"]

                tf_workspace_add_vcs = TerraformApi.workspace_add_repo(TF_TOKEN, tf_workspace_id, gitlab_project_url,
                                                                       OAUTH_TOKEN_ID)
                tf_workspace_add_vcs.raise_for_status()

            # SETTING UP WORKSPACE VARIABLES AND VARIABLE SETS #
            # Set variables of workspace (TFvars)
            tf_workspace_var_check = TerraformApi.workspace_var_get(TF_TOKEN, TF_ORG, tf_workspace_name)

            if not tf_workspace_var_check["data"]:
                for field in matching_field:
                    if (field != "Environment") and (field != "workspace_name"):
                        tf_workspace_var_create = TerraformApi.workspace_var_create(TF_TOKEN, field, matching_field[field],
                                                                                    tf_workspace_id)
                        tf_workspace_var_create.raise_for_status()
                    else:
                        continue
            else:
                tf_workspace_matching_vars = []
                for var in tf_workspace_var_check["data"]:
                    if var["attributes"]["key"] in matching_field:
                        k = var["attributes"]["key"]
                        v = matching_field[k]
                        tf_workspace_matching_vars.append(k)
                        if var["attributes"]["value"] != v:
                            TerraformApi.workspace_var_update(TF_TOKEN, var["id"], k, v)
                        else:
                            continue

                for k in matching_field:
                    v = matching_field[k]
                    if (k != "Environment") and (k != "workspace_name"):
                        if k not in tf_workspace_matching_vars:
                            TerraformApi.workspace_var_create(TF_TOKEN, k, v, tf_workspace_id)
                        else:
                            continue

            tf_varset_workspace_list = []
            for workspace in tf_varset_relationships:
                if tf_workspace_id == workspace["id"]:
                    tf_varset_workspace_list.append(workspace["id"])
                    break
                else:
                    tf_varset_workspace_list.append(workspace["id"])
                    continue

            if tf_workspace_id not in tf_varset_workspace_list:
                workspace_varset = TerraformApi.workspace_varset_set(TF_TOKEN, tf_varset_id,
                                                                     workspace_id=tf_workspace_id)
                workspace_varset.raise_for_status()

            # Create workspace notification config
            tf_team_id = TerraformApi.tf_team_get(TF_TOKEN, "owners", TF_ORG)
            tf_user_id_list = TerraformApi.tf_team_member_get(TF_TOKEN, tf_team_id)
            TerraformApi.tf_notification_set(TF_TOKEN, tf_workspace_id, tf_user_id_list)

            # TERRAFORM RUN
            # After finished setting up Terraform workspace, workspace variable, variable set, create the Terraform run
            # Terraform created by this script set the auto-apply == false, so after Terraform plan,
            # it will wait for confirmation
            tf_run = TerraformApi.workspace_run(TF_TOKEN, tf_workspace_id)
            tf_run.raise_for_status()

            # Because SDP only script run up to 60 seconds, so we pass data into a temp file and
            # Create folder
            temp_folder = os.path.join(cur_dir, "../temp/")
            folder = common.folder_create(tf_workspace_name, temp_folder)
            # Save run data so new process have something to do
            temp_file = os.path.join(folder, "temp.json")
            with open(f"{temp_file}", "w") as file:
                file.write(tf_run.text)

            # Gather some data into file for new process
            data = {
                "tf_workspace_name": tf_workspace_name,
                "change_id": opt_data["INPUT_DATA"]["entity_data"]["template"]["id"]
            }
            data = str(data)

            data_file = os.path.join(folder, "data.json")
            with open(data_file, "w") as file:
                file.write(data)

            # file path to the next script
            next_script = os.path.join(cur_dir, "TerraformRunFetchStatus.py")

            # Check platform
            if sys.platform == "win32":
                # create a new independent process
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                DETACHED_PROCESS = 0x00000008

                Popen([f"python {next_script} {folder}"],
                      stdin=None, stdout=None, stderr=None, shell=True,
                      creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
            else:
                Popen([f"python3 {next_script} {folder}"],
                      stdin=None, stdout=None, stderr=None, shell=True)
