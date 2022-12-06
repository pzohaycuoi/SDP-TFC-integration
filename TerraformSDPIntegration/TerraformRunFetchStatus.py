import json
import os
import TerraformApi
import common
import time
from dotenv import load_dotenv
import SDP
import sys


# folder = sys.argv[1]  # Get folder path, created by TerraformSDIntegration.py
folder = "C:/Users/namng/OneDrive/Code/Python/TerraformSDPIntegration/temp/test_workspace88-dev-06-12-2022-12-51-19"
cur_dir = os.path.dirname(__file__)
temp_file = os.path.join(folder, "temp.json")
data_file = os.path.join(folder, "data.json")

# load .env file and
# check if TOKEN and TF_ORG have value
TF_TOKEN, TF_ORG, GITLAB_TOKEN, GITLAB_REPO_ID, GITLAB_NAMESPACE, REPO, OAUTH_TOKEN_ID, SDP_TOKEN, SDP_SERVER \
    = common.dotenv_load()

# Get data from data file
with open(data_file) as file:
    temp_data = file.read()
    temp_data = json.loads(temp_data)
    tf_workspace_name = temp_data["tf_workspace_name"]
    change_id = temp_data["change_id"]

# Create SDP ticket
task_name = f"{tf_workspace_name}-Terraform-plan"
task_plan_id = SDP.task_add(SDP_TOKEN, change_id, task_name, f"{tf_workspace_name} Terraform plan detail")

# Get data from the temp file
with open(temp_file) as file:
    run_detail = file.read()
    run_detail = json.loads(run_detail)
    run_id = run_detail["data"]["id"]

# Timestamp start the plan phase
time_start = time.time()

# List of pending status
status_pending_list = ["fetching", "queuing", "planning", "cost_estimating", "policy_checking",
                       "post_plan_running", "applying", "apply_queued", "plan_queued", "queuing", "pre_plan_running"]
status_completed_list = ["fetching_completed", "pre_plan_completed", "planned", "cost_estimated", "confirmed",
                         "post_plan_completed", "planned_and_finished", "applied"]
status_plan_completed_list = ["pending", "planned", "cost_estimated"]
status_error_list = ["discarded", "errored", "canceled", "force_canceled"]

# Loop until Terraform run completed
# When Terraform run initialized, it will start plan first, after that will get on to pending state
# On pending state, when SDP ticket get all approval from CABs will trigger another script
# to start Terraform apply run.
i = 0
while True:
    if i < 180:  # 30 minutes
        run_detail = TerraformApi.tf_run_get(TF_TOKEN, run_id)
        run_detail.raise_for_status()
        run_detail = json.loads(run_detail.content)
        if run_detail["data"] is None:
            time.sleep(2)
            continue
        else:
            run_status = run_detail["data"]["attributes"]["status"]
            if run_status in status_pending_list:
                time.sleep(10)
                continue
            elif run_status in status_error_list:
                time_end = time.time()
                SDP.worklog_add(SDP_TOKEN, SDP_SERVER, task_plan_id, f"{tf_workspace_name} plan failed: {run_status}",
                                time_start, time_end)
                SDP.task_update(SDP_TOKEN, task_plan_id, "Cancelled")
                raise SystemExit("An error occurred with Terraform plan, exiting")
            elif run_status in status_plan_completed_list:
                time_end = time.time()
                SDP.worklog_add(SDP_TOKEN, SDP_SERVER, task_plan_id, f"{tf_workspace_name} plan failed: time out",
                                time_start, time_end)
                SDP.task_update(SDP_TOKEN, task_plan_id, "Closed")
                break

    else:
        time_end = time.time()
        SDP.worklog_add(SDP_TOKEN, SDP_SERVER, task_plan_id, f"{tf_workspace_name} plan failed: time out",
                        time_start, time_end)
        SDP.task_update(SDP_TOKEN, task_plan_id, "Cancelled")
        raise SystemExit("Time out for TF plan exceeded, exiting")

# After successfully fetch the plan completed status of Terraform
# TODO: add trigger to SDP API
print("cac")