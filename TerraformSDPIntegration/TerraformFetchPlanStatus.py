import json
import os
import TerraformApi
import common
import time
import SDPAPI
import sys

# folder = sys.argv[1]  # Get folder path, created by TerraformSDIntegration.py
folder = '../temp/test_workspace895-dev-07-12-2022-15-19-38'
cur_dir = os.path.dirname(__file__)
temp_file = os.path.join(folder, "temp.json")
data_file = os.path.join(folder, "data.json")

# load .env file and
TF_TOKEN, TF_ORG, GITLAB_TOKEN, GITLAB_REPO_ID, GITLAB_NAMESPACE, REPO, OAUTH_TOKEN_ID, SDP_TOKEN, SDP_SERVER, \
    TF_SERVER, GITLAB_SERVER = common.dotenv_load()

# Get data from data file
with open(data_file) as file:
    temp_data = file.read()
    temp_data = json.loads(temp_data)
    workspace_name = temp_data["workspace_name"]
    change_id = temp_data["change_id"]

# Get data from the temp file
with open(temp_file) as file:
    run_detail = file.read()
    run_detail = json.loads(run_detail)
    run_id = run_detail["data"]["id"]
    plan_id = run_detail["data"]["relationships"]["plan"]["data"]["id"]

# Create SDP task
task_name = f"{workspace_name}-Terraform-plan"
task_plan_id = SDPAPI.task_add(SDP_TOKEN, SDP_SERVER, change_id, task_name, f"{workspace_name}-{run_id}-Terraform plan detail")

# Timestamp start the plan phase
time_start = round(time.time() * 1000)

# List of pending status
status_pending_list = ["fetching", "queuing", "planning", "cost_estimating", "policy_checking", "pending"
                       "post_plan_running", "applying", "apply_queued", "plan_queued", "queuing", "pre_plan_running"]
status_completed_list = ["fetching_completed", "pre_plan_completed", "confirmed", "post_plan_completed",
                         "cost_estimated", "planned_and_finished"]
status_final_completed_list = ["applied"]
status_plan_completed_list = ["planned"]
status_error_list = ["discarded", "errored", "canceled", "force_canceled"]

# Loop until Terraform run completed
# When Terraform run initialized, it will start plan first, after that will get on to pending state
# On pending state, when SDP ticket get all approval from CABs will trigger another script
# to start Terraform apply run.
i = 0
while True:
    i += 1
    if i < 180:  # 30 minutes
        run_detail = TerraformApi.tf_run_get(TF_TOKEN, TF_SERVER, run_id)
        if run_detail["data"] is None:
            time.sleep(10)
            continue
        else:
            run_status = run_detail["data"]["attributes"]["status"]
            if run_status in status_pending_list:
                time.sleep(10)
                continue
            elif run_status in status_error_list:
                time_end = round(time.time() * 1000)
                SDPAPI.worklog_add(SDP_TOKEN, SDP_SERVER, task_plan_id, f"{workspace_name} plan failed: {run_status}",
                                   time_start, time_end)
                SDPAPI.task_update(SDP_TOKEN, SDP_SERVER, task_plan_id, "Cancelled")
                raise SystemExit("An error occurred with Terraform plan, exiting")
            elif run_status in status_plan_completed_list:
                time_end = round(time.time() * 1000)
                SDPAPI.worklog_add(SDP_TOKEN, SDP_SERVER, task_plan_id, f"{workspace_name} plan completed",
                                   time_start, time_end)
                break
            else:
                time.sleep(10)
    else:
        time_end = round(time.time() * 1000)
        SDPAPI.worklog_add(SDP_TOKEN, SDP_SERVER, task_plan_id, f"{workspace_name} plan failed: time out",
                           time_start, time_end)
        SDPAPI.task_update(SDP_TOKEN, SDP_SERVER, task_plan_id, "Cancelled")
        raise SystemExit("Time out for TF plan exceeded, exiting")

# After successfully fetch the plan completed status of Terraform
# Get Terraform plan detail and attach it to the SDP task
plan_result_file_path = os.path.join(folder, f"{workspace_name}-{run_id}-plan.json")
plan_result_file = TerraformApi.tf_plan_to_file(TF_TOKEN, TF_SERVER, run_id, plan_result_file_path)
SDPAPI.task_attachment_add(SDP_TOKEN, SDP_SERVER, task_plan_id, plan_result_file)
SDPAPI.task_update(SDP_TOKEN, SDP_SERVER, task_plan_id, "Closed")