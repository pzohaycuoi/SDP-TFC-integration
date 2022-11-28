import json
import os
import TerraformApi
from dotenv import load_dotenv


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
# Get data from the file
with open("../temp/temp.json") as file:
    run_detail = file.read()
    run_detail = json.loads(run_detail)

run_id = run_detail["data"]["id"]
run_status = TerraformApi.tf_run_get(TOKEN, run_id)
run_status.raise_for_status()

