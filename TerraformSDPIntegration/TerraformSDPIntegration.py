from dotenv import load_dotenv
import os
import json
import TerraformApi
import SDP
import VCS
import tarfile
import glob
import stat


# load $COMPLETE_JSON_FILE from SDP
# input_file = sys.argv[1]
input_file = '../test/test-data.json'
try:
    opt_data = SDP.convert_json(input_file)
except AssertionError as err:
    raise SystemExit(err)

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
else:
    # Get Terraform code from repository
    repo = VCS.git_clone(REPO, "../temp")
    repo_dir = repo.git_dir.replace(".git", "")
    # files = glob.glob(repo.git_dir)
    # for f in files:
    #     os.chmod(f, stat.S_IWRITE)
    #     os.remove(f)

    repo_name = repo.remotes.origin.url.split('.git')[0].split('/')[-1]
    tar_file = f"../temp/{repo_name}.tar.gz"
    with tarfile.open(tar_file, "w:gz") as tar:
        tar.add(repo_dir, arcname=os.path.basename(repo_dir))

    var_files = VCS.find_all("variables.tf", "../temp")
    # get variable list
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
    for field in field_list:
        if field in matching_field_name:
            matching_field.update({field: field_list[field]})
        elif field == "workspace_name":
            matching_field.update({field: field_list[field]})

    # Check if workspace field hs value
    ws_name = matching_field["workspace_name"]
    if (ws_name == '') or (ws_name is None):
        SystemExit("No Terraform workspace name provided, exiting...")
    else:
        # TODO: Check if workspace is created
        ws_get = TerraformApi.workspace_get(TOKEN, TF_ORG, ws_name)
        if ws_get.status_code == 400:
            SystemExit("User token does not have permission or token invalid")
        elif ws_get.status_code == 200:
            # TODO: If Workspace already exist then use this workspace instead of throw error
            SystemExit("Terraform workspace name is already exist, please pick other name, exiting...")
        else:
            # Create Terraform workspace
            ws_create = TerraformApi.workspace_create(TOKEN, TF_ORG, ws_name, auto_apply=False)
            ws_create.raise_for_status()
            ws_create_content = json.loads(ws_create.content)
            # TODO: If workspace is already created, check if workspace have configuration version
            # Create Terraform configuration version
            ws_conf_create = TerraformApi.workspace_config_create(TOKEN, ws_create_content["data"]["id"],
                                                                  auto_queue=False)
            ws_conf_create.raise_for_status()
            ws_conf_content = json.loads(ws_conf_create.content)
            # Get upload url from configuration version and upload Terraform code into workspace
            ws_conf_upload = TerraformApi.workspace_upload_code(TOKEN, tar_file,
                                                                ws_conf_content["data"]["attributes"]["upload-url"])

# # get upload url from the configuration version
# ws_conf_upload_url = ws_conf_content["data"]["attributes"]["upload-url"]
# # upload configuration content file
# tar_file = [('file', open('../repo.tar.gz', 'rb'))]
# ws_upload_file_payload = {}
# ws_upload_file_response = api_request(ws_conf_upload_url, TOKEN, "PUT", {}, tar_file)
# print(ws_upload_file_response.text)
