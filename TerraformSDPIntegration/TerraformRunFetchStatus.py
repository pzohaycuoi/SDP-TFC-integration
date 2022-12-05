import json
import os
import TerraformApi
import common
import time
from dotenv import load_dotenv


# load .env file and
# check if TOKEN and TF_ORG have value
TF_TOKEN, TF_ORG, GITLAB_TOKEN, GITLAB_REPO_ID, GITLAB_NAMESPACE, REPO, OAUTH_TOKEN_ID = common.dotenv_load()
# Get data from the file
with open("../temp/temp.json") as file:
    run_detail = file.read()
    run_detail = json.loads(run_detail)
    run_id = run_detail["data"]["id"]

# list of pending status
status_pending_list = ["pending", "fetching", "queuing", "planning", "cost_estimating", "policy_checking",
                       "post_plan_running", "applying", "apply_queued", "plan_queued", "queuing", "pre_plan_running"]
status_completed_list = ["fetching_completed", "pre_plan_completed", "planned", "cost_estimated", "confirmed",
                         "post_plan_completed", "planned_and_finished", "applied"]
status_plan_completed_list = []
status_error_list = ["discarded", "errored", "canceled", "force_canceled"]

# Loop until Terraform run completed
# When Terraform run initialized, it will start plan first, after that will get on to pending state
# On pending state, when SDP ticket get all approval from CABs will trigger another script
# to start Terraform apply run.
i = 0
while True:
    if i < 7:
        run_detail = TerraformApi.tf_run_get(TF_TOKEN, run_id)
        run_detail.raise_for_status()
        run_detail = json.loads(run_detail)
        if run_detail["data"] is None:
            time.sleep(5)
            continue
        else:
            run_status = run_detail["attributes"]["status"]
            if run_status in status_pending_list:
                time.sleep(5)
                continue
            elif run_status in status_error_list:
                break
            elif run_status in status_plan_completed_list:
                # TODO: fetch run status


    else:
        break

# After successfully fetch the plan completed status of Terraform
# Create 1 new task
# TODO: add trigger to SDP API
