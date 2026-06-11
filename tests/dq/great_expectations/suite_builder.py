import json
import great_expectations as gx
from great_expectations.core.batch import BatchRequest
from datetime import date
from config import GX_ROOT
import sys
sys.path.insert(0, "/workspaces/Test_Automation_Fincore_Backup/tests/dq/great_expectations/gx/plugins")
import expect_end_date_after_start_date

CONFIG_PATH = "/workspaces/Test_Automation_Fincore_Backup/tests/dq/great_expectations/rules_config.json"

with open(CONFIG_PATH) as f:
    config = json.load(f)

context = gx.get_context(context_root_dir=GX_ROOT)

for table in config["tables"]:
    suite_name = table["suite_name"]
    table_name = table["table_name"]

    suite = context.add_or_update_expectation_suite(expectation_suite_name=suite_name)

    # get validator
    batch_request = BatchRequest(
    datasource_name=config["datasource_name"],
    data_connector_name=config["data_connector_name"],
    data_asset_name=table_name
    )

    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name
    )

    print(f"Validator ready for: {table_name}")
    
    for expectations in table["expectations"]:
        if expectations["type"] == "SKIP_custom":
            print(f"Skipping: {expectations.get('comment', '')}")
            continue

        if expectations.get("max_value") == "today":
            expectations["max_value"] = str(date.today())
        if expectations.get("min_value") == "today":
            expectations["min_value"] = str(date.today())

        params = {k: v for k, v in expectations.items() if k != "type"}
        expectation_fn = getattr(validator, expectations["type"])
        expectation_fn(**params)

    validator.save_expectation_suite(discard_failed_expectations=False)
    print(f"Suite saved: {suite_name}")
	